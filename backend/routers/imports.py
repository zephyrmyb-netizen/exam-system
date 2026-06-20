import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

from .. import auth as auth_module
from .. import crud, schemas
from ..config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from ..crud import derive_course_name_from_filename
from ..database import get_db
from ..models import Question as QuestionModel

router = APIRouter(prefix="/imports", tags=["imports"])

ALLOWED_EXTENSIONS = {".docx", ".pptx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def extract_text_from_file(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    if ext == ".docx":
        from docx import Document
        doc = Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    elif ext == ".pptx":
        from pptx import Presentation
        prs = Presentation(file_path)
        texts = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    texts.append(shape.text)
        return "\n".join(texts)
    raise ValueError(f"不支持的文件格式: {ext}")


@router.post("/file", response_model=schemas.FileExtractResponse)
async def upload_file(
    file: UploadFile = File(...),
    course_id: int = Query(0, ge=0, description="目标课程ID（0表示自动创建/使用「未分类题库」）"),
    db: Session = Depends(get_db),
    _current_user=Depends(auth_module.get_current_user),
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式 '{ext}'，仅支持 .docx 或 .pptx 文件",
        )

    # Check file size before reading
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"文件大小超过限制（最大 {MAX_FILE_SIZE // (1024*1024)}MB）",
        )

    tmp_path = None
    try:
        suffix = ext or ".tmp"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        if ext == ".docx":
            from docx import Document
            doc = Document(tmp_path)
            text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        elif ext == ".pptx":
            from pptx import Presentation
            prs = Presentation(tmp_path)
            texts = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        texts.append(shape.text)
            text = "\n".join(texts)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")

        return schemas.FileExtractResponse(
            text=text,
            filename=file.filename or "unknown",
            suggested_course_name=derive_course_name_from_filename(file.filename or ""),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件提取失败: {str(e)}")
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


@router.post("/file/auto")
async def import_file_auto(
    file: UploadFile = File(...),
    course_id: int = Query(0, ge=0, description="目标课程ID（0表示使用 course_name 或文件名推断）"),
    course_name: str = Query("", description="目标课程名（course_id=0 时优先使用；空则从文件名推断）"),
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式 '{ext}'，仅支持 .docx 或 .pptx 文件",
        )

    # Check file size before reading
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"文件大小超过限制（最大 {MAX_FILE_SIZE // (1024*1024)}MB）",
        )

    tmp_path = None
    try:
        suffix = ext or ".tmp"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        text = extract_text_from_file(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件提取失败: {str(e)}")
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    if not text.strip():
        raise HTTPException(status_code=400, detail="文件中未提取到任何文本内容")

    # Resolve target course — priority:
    #   1. course_id > 0           → use the specified course
    #   2. course_name is non-blank → find-or-create by that name
    #   3. derive from filename     → derive_course_name_from_filename()
    #   4. fallback                 → 未分类题库
    try:
        if course_id > 0:
            bank, _ = crud.resolve_course(db, current_user.id, course_id=course_id)
        elif course_name.strip():
            bank, _ = crud.resolve_course(db, current_user.id, course_name=course_name.strip())
        else:
            derived = derive_course_name_from_filename(file.filename or "")
            bank, _ = crud.resolve_course(db, current_user.id, course_name=derived)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # If no OpenAI key, return clear error
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=400,
            detail="未配置 OPENAI_API_KEY，请在 .env 文件中设置 OPENAI_API_KEY 以使用 AI 自动导入功能",
        )

    # Call OpenAI-compatible API to structure the extracted text into questions
    try:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        prompt = (
            "你是一个题目解析助手。请将以下教育文档内容解析为 JSON 数组，每道题为一个对象。\n\n"
            "支持的题目类型：\n"
            "- single_choice（单选题）\n"
            "- multiple_choice（多选题）\n"
            "- true_false（判断题）\n"
            "- fill_blank（填空题）\n"
            "- short_answer（简答题）\n\n"
            "每个对象字段：\n"
            "- type: 题目类型（必填）\n"
            "- question: 题目题干（必填）\n"
            "- options: 选择题的选项字典，如 {\"A\": \"内容1\", \"B\": \"内容2\"}（选择题必填）\n"
            "- answer: 正确答案（必填）\n"
            "- analysis: 解析（可选）\n"
            "- subject: 科目（可选，默认\"默认科目\"）\n"
            "- chapter: 章节（可选，默认\"默认章节\"）\n"
            "- difficulty: 难度 easy/normal/hard（可选，默认\"normal\"）\n\n"
            "请以 JSON 格式输出，包含一个 questions 字段，其值为题目数组。\n"
            '示例：{"questions": [{"type": "single_choice", "question": "...", "options": {"A": "...", "B": "..."}, "answer": "A"}]}\n\n'
            f"文档内容：\n{text[:10000]}"
        )

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        raw = response.choices[0].message.content
        if not raw:
            raise ValueError("AI 返回了空响应，请检查 API 密钥和模型是否可用")

        import json
        parsed = json.loads(raw)

        # Extract the questions list from various possible response shapes
        if isinstance(parsed, list):
            questions_list = parsed
        elif isinstance(parsed, dict):
            questions_list = (
                parsed.get("questions")
                or parsed.get("items")
                or parsed.get("data")
                or parsed.get("result")
                or []
            )
            if not questions_list and parsed:
                if "question" in parsed or "type" in parsed:
                    questions_list = [parsed]
        else:
            questions_list = []

        if not questions_list:
            raise ValueError(
                "AI 返回了无法解析的数据结构。请检查文档内容是否包含有效的题目信息。"
                f"原始返回：{raw[:300]}"
            )

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=502,
            detail=f"AI 返回了非 JSON 格式内容，无法解析。原始返回：{(raw or '')[:200]}",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI 服务调用失败: {str(e)}")

    # Validate and import into the user's course
    imported = 0
    errors = []
    for i, item in enumerate(questions_list):
        try:
            q_data = schemas.QuestionCreate(
                type=item.get("type", "fill_blank"),
                question=item.get("question", ""),
                options=item.get("options"),
                answer=item.get("answer", ""),
                analysis=item.get("analysis", ""),
                subject=item.get("subject", "默认科目"),
                chapter=item.get("chapter", "默认章节"),
                difficulty=item.get("difficulty", "normal"),
            )
            from ..models import Question as QuestionModel
            from ..utils import normalize_answer

            question = QuestionModel(
                owner_id=current_user.id,
                course_id=bank.id,
                visibility="private",
                source="import",
                created_at=datetime.now(timezone.utc),
                subject=q_data.subject,
                chapter=q_data.chapter,
                type=q_data.type,
                question=q_data.question,
                answer=normalize_answer(q_data.answer, q_data.type),
                analysis=q_data.analysis or "",
                difficulty=q_data.difficulty or "normal",
            )
            question.set_options_dict(q_data.options)
            db.add(question)
            imported += 1
        except Exception as exc:
            errors.append(f"第 {i+1} 题导入失败: {exc}")

    if imported > 0:
        db.commit()

    return schemas.FileAutoResponse(imported_count=imported, course_id=bank.id, course_name=bank.name)
