import json as json_module
import os
import re
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile
from openai import APIConnectionError, APIStatusError, OpenAI
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..config import (
    IMPORT_BATCH_SIZE,
    IMPORT_CHUNK_SIZE,
    IMPORT_MAX_TOKENS,
    IMPORT_UPSTREAM_TIMEOUT,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
)
from ..crud import derive_course_name_from_filename
from ..models import Question as QuestionModel
from ..utils import VALID_QUESTION_TYPES, normalize_answer
from .image_extractor import IMAGE_EXTENSIONS, ImagePayload, extract_images_from_file, image_bytes_to_data_url

try:
    from openai import APITimeoutError
except ImportError:  # pragma: no cover
    APITimeoutError = TimeoutError


ALLOWED_EXTENSIONS = {".docx", ".pdf", ".pptx", ".png", ".jpg", ".jpeg", ".webp"}
LEGACY_PPT_EXTENSION = ".ppt"
MAX_FILE_SIZE = 10 * 1024 * 1024
AI_CHUNK_SIZE = max(1000, IMPORT_CHUNK_SIZE)
# This deliberately bounds one sequential batch, not the whole document.  A
# long file must not silently lose every chunk after the first batch.
AI_BATCH_SIZE = max(1, IMPORT_BATCH_SIZE)
AI_MAX_TOKENS = max(1000, IMPORT_MAX_TOKENS)
AI_IMAGE_BATCH_SIZE = 3
MAX_NUMBERED_QUESTIONS_PER_CHUNK = 6
RETRY_NUMBERED_QUESTIONS_PER_CHUNK = 2
AI_CHUNK_MAX_ATTEMPTS = 2
MIN_NUMBERED_QUESTION_COVERAGE_RATIO = 0.8
# A document-level question start is deliberately stricter than the legacy AI
# chunking boundary below. In particular, ``(1)`` and ``①`` are content of
# the current question, never independent questions.
_TOP_LEVEL_QUESTION_LINE = re.compile(r"^\s*(?P<number>\d{1,4})\s*[.．、]\s*(?P<body>.*\S)?\s*$")
_SECTION_HEADING_LINE = re.compile(r"^\s*[一二三四五六七八九十百]+、\s*(?P<title>.+?)\s*$")
_OPTION_LINE = re.compile(r"^\s*(?P<key>[A-Ha-h])\s*[.．、:：]\s*(?P<value>.*\S)\s*$")
_ANSWER_LINE = re.compile(r"^\s*(?:参考)?答案\s*[:：]\s*(?P<value>.*)\s*$", re.IGNORECASE)
_ANALYSIS_LINE = re.compile(r"^\s*(?:答案)?解析\s*[:：]\s*(?P<value>.*)\s*$", re.IGNORECASE)
_SOLUTION_LINE = re.compile(r"^\s*解\s*[:：]\s*(?P<value>.*)\s*$")
_NUMBERED_QUESTION_BOUNDARY = re.compile(r"(?<!\S)(?:\d{1,4}[.、．)]|[（(]\d{1,4}[）)])\s*")
ParseProgressCallback = Callable[[list[dict[str, Any]], list[str], dict[str, Any]], None]


@dataclass
class SavedUpload:
    filename: str
    ext: str
    path: str


def elapsed_ms(start: float) -> int:
    return max(0, round((time.perf_counter() - start) * 1000))


def build_timing(
    *,
    total_start: float,
    extract_ms: int = 0,
    parse_timing: dict | None = None,
) -> schemas.ImportTiming:
    parse_timing = parse_timing or {}
    return schemas.ImportTiming(
        extract_ms=extract_ms,
        chunk_ms=int(parse_timing.get("chunk_ms") or 0),
        ai_ms=int(parse_timing.get("ai_ms") or 0),
        total_ms=elapsed_ms(total_start),
        chunks=int(parse_timing.get("chunks") or 0),
        ai_chunks=list(parse_timing.get("ai_chunks") or []),
        completed_chunks=int(parse_timing.get("completed_chunks") or 0),
        failed_chunks=int(parse_timing.get("failed_chunks") or 0),
        batches=int(parse_timing.get("batches") or 0),
        is_complete=bool(parse_timing.get("is_complete", True)),
    )


def _ai_override_active() -> bool:
    """Return True when tests have injected a fake OpenAI class."""
    return OpenAI is not __import__("openai").OpenAI


def validate_upload_extension(filename: str) -> str:
    """Validate the file extension only (no size check). Returns the lowercased ext.

    Use this before streaming to avoid reading the file when the format is
    outright unsupported.
    """
    ext = Path(filename or "").suffix.lower()
    if ext == LEGACY_PPT_EXTENSION:
        raise HTTPException(
            status_code=400,
            detail="暂不支持旧版 .ppt，请在 PowerPoint/WPS 中另存为 .pptx 后上传。",
        )
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式 '{ext}'，仅支持 .docx、.pdf、.pptx、.png、.jpg、.jpeg、.webp 文件",
        )
    return ext


def validate_upload(filename: str, content: bytes) -> str:
    """Validate both extension and size of an in-memory upload.

    Kept for backward compatibility with callers that already hold the bytes
    (e.g. tests). New code should prefer :func:`validate_upload_extension`
    plus streaming size checks in :func:`save_upload_to_temp`.
    """
    ext = validate_upload_extension(filename)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"文件大小超过限制（最大 {MAX_FILE_SIZE // (1024 * 1024)}MB）",
        )
    return ext


def detect_file_kind(filename_or_path: str) -> str:
    ext = Path(filename_or_path or "").suffix.lower()
    if ext == ".docx":
        return "docx"
    if ext == ".pdf":
        return "pdf"
    if ext == ".pptx":
        return "pptx"
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext == LEGACY_PPT_EXTENSION:
        return "legacy_ppt"
    return "unsupported"


# 流式上传分块大小：64KB，平衡 I/O 次数与内存占用
_UPLOAD_CHUNK_SIZE = 64 * 1024


async def save_upload_to_temp(file: UploadFile) -> SavedUpload:
    """Stream an upload to a temp file in chunks, enforcing the size limit.

    Avoids loading the entire file into memory before validation. The
    extension is checked up front (cheap, no I/O); size is enforced
    incrementally while writing chunks — exceeding the limit aborts early
    and the partial temp file is removed.
    """
    filename = file.filename or "unknown"
    ext = validate_upload_extension(filename)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext or ".tmp")
    path = tmp.name
    written = 0
    try:
        tmp.close()
        with open(path, "wb") as out:
            while True:
                chunk = await file.read(_UPLOAD_CHUNK_SIZE)
                if not chunk:
                    break
                written += len(chunk)
                if written > MAX_FILE_SIZE:
                    out.close()
                    os.unlink(path)
                    raise HTTPException(
                        status_code=413,
                        detail=f"文件大小超过限制（最大 {MAX_FILE_SIZE // (1024 * 1024)}MB）",
                    )
                out.write(chunk)
    except HTTPException:
        raise
    except Exception:
        # Clean up the partial temp file on any other failure.
        try:
            os.unlink(path)
        except OSError:
            pass
        raise
    return SavedUpload(filename=filename, ext=ext, path=path)


def cleanup_temp_file(path: str | None) -> None:
    if not path:
        return
    try:
        os.unlink(path)
    except OSError:
        pass


def extract_text_and_warnings(file_path: str) -> tuple[str, list[str]]:
    ext = Path(file_path).suffix.lower()
    warnings: list[str] = []
    if ext == ".docx":
        return _extract_docx(file_path, warnings)
    if ext == ".pdf":
        return _extract_pdf(file_path, warnings)
    if ext == ".pptx":
        return _extract_pptx(file_path, warnings)
    if ext in IMAGE_EXTENSIONS:
        return "", warnings
    if ext == LEGACY_PPT_EXTENSION:
        raise HTTPException(status_code=400, detail="暂不支持旧版 .ppt，请在 PowerPoint/WPS 中另存为 .pptx 后上传。")
    raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}")


def empty_extract_detail(file_path: str, warnings: list[str] | None = None) -> str:
    ext = Path(file_path).suffix.lower()
    if warnings:
        return "；".join(warnings[:3])
    if ext == ".pdf":
        return "未从 PDF 中提取到文字，请确认不是扫描版图片 PDF，或将页面导出为图片后上传。"
    if ext == ".pptx":
        return "未从 PPTX 中识别到文字或图片题目，请检查文件是否为空，或尝试导出为图片后上传。"
    if ext in IMAGE_EXTENSIONS:
        return "图片识别失败，请确认图片格式正确且内容清晰。"
    return "文档中未提取到任何文本内容"


def _extract_docx(path: str, warnings: list[str]) -> tuple[str, list[str]]:
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    doc = Document(path)
    parts: list[str] = []

    def table_rows(table: Table) -> list[str]:
        rows: list[str] = []
        for row in table.rows:
            cells: list[str] = []
            for cell in row.cells:
                paragraphs = [paragraph.text.strip() for paragraph in cell.paragraphs if paragraph.text.strip()]
                nested = [text for nested_table in cell.tables for text in table_rows(nested_table)]
                cell_text = "\n".join(paragraphs + nested)
                if cell_text:
                    cells.append(cell_text)
            if cells:
                rows.append(" | ".join(cells))
        return rows

    # Iterate the XML body so ordinary paragraphs and tables remain in their
    # original interleaved order. Reading doc.paragraphs then doc.tables loses
    # that order and can split an answer from its question.
    for child in doc.element.body.iterchildren():
        if child.tag.endswith("}p"):
            text = Paragraph(child, doc).text.strip()
            if text:
                parts.append(text)
        elif child.tag.endswith("}tbl"):
            parts.extend(table_rows(Table(child, doc)))

    return "\n".join(parts), warnings


def _section_question_type(title: str) -> str | None:
    """Map a Word section heading to a supported question type."""
    normalized = (title or "").replace(" ", "")
    if "多项" in normalized or "多选" in normalized:
        return "multiple_choice"
    if "单项" in normalized or "单选" in normalized:
        return "single_choice"
    if "判断" in normalized:
        return "true_false"
    if "填空" in normalized:
        return "fill_blank"
    if any(keyword in normalized for keyword in ("名词解释", "简答", "计算", "讨论", "论述", "问答")):
        return "short_answer"
    return None


def _infer_rule_question_type(
    section_type: str | None,
    options: dict[str, str],
    answer: str,
) -> str:
    if section_type in VALID_QUESTION_TYPES:
        return section_type
    if len(options) >= 2:
        return "single_choice"
    normalized_answer = (answer or "").strip().lower()
    if normalized_answer in {"true", "false", "yes", "no", "对", "错", "正确", "错误", "是", "否"}:
        return "true_false"
    return "short_answer"


def _rule_question_from_block(
    *,
    number: int,
    body_lines: list[str],
    section_title: str,
    section_type: str | None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Build one import question from a complete top-level numbered block."""
    stem_lines: list[str] = []
    answer_lines: list[str] = []
    analysis_lines: list[str] = []
    options: dict[str, str] = {}
    target = stem_lines

    for raw_line in body_lines:
        # Word exports often put ``题干 答案：A`` in one paragraph. Split that
        # deterministic delimiter before interpreting the line state.
        inline_marker = re.search(r"\s+((?:参考)?答案|(?:答案)?解析|解)\s*[:：]", raw_line)
        pieces = (
            [raw_line[: inline_marker.start()], raw_line[inline_marker.start() :]]
            if inline_marker
            else [raw_line]
        )
        for raw_piece in pieces:
            line = raw_piece.strip()
            if not line:
                continue
            answer_match = _ANSWER_LINE.match(line)
            analysis_match = _ANALYSIS_LINE.match(line) or _SOLUTION_LINE.match(line)
            option_match = _OPTION_LINE.match(line)
            if analysis_match:
                target = analysis_lines
                if analysis_match.group("value").strip():
                    target.append(analysis_match.group("value").strip())
                continue
            if answer_match:
                target = answer_lines
                if answer_match.group("value").strip():
                    target.append(answer_match.group("value").strip())
                continue
            if option_match and target is stem_lines:
                options[option_match.group("key").upper()] = option_match.group("value").strip()
                continue
            target.append(line)

    question = "\n".join(stem_lines).strip()
    answer = "\n".join(answer_lines).strip()
    question_type = _infer_rule_question_type(section_type, options, answer)
    item: dict[str, Any] = {
        "type": question_type,
        "question": question,
        "options": options or None,
        "answer": answer,
        "analysis": "\n".join(analysis_lines).strip(),
        "subject": "默认科目",
        "chapter": section_title or "默认章节",
        "difficulty": "normal",
        "line_number": number,
    }
    validated, error = validate_question_item(item)
    if validated is None:
        return None, error
    validated["line_number"] = number
    return validated, None


def parse_rule_based_question_document(
    text: str,
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]] | None:
    """Parse regular numbered Word-style question banks without asking AI.

    This parser intentionally accepts only a sequence starting at ``1.`` (or
    Chinese punctuation variants). Once selected, a non-contiguous top-level
    number makes the preview partial rather than silently turning a subquestion
    into another question. Free-form documents still use the AI fallback.
    """
    start = time.perf_counter()
    blocks: list[tuple[int, list[str], str, str | None]] = []
    warnings: list[str] = []
    current_lines: list[str] | None = None
    current_number: int | None = None
    current_section = ""
    current_section_type: str | None = None
    expected_number = 1
    saw_top_level = False
    sequence_error = False

    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        heading_match = _SECTION_HEADING_LINE.match(line)
        if heading_match:
            current_section = heading_match.group("title").strip()
            current_section_type = _section_question_type(current_section)
            continue

        question_match = _TOP_LEVEL_QUESTION_LINE.match(line)
        if question_match:
            number = int(question_match.group("number"))
            if not saw_top_level and number != 1:
                return None
            saw_top_level = True
            if number != expected_number:
                sequence_error = True
                warnings.append(
                    f"检测到题号 {number}，但当前应为 {expected_number}；已保留预览但禁止确认导入。"
                )
                if current_lines is not None:
                    current_lines.append(line)
                continue
            if current_lines is not None and current_number is not None:
                blocks.append((current_number, current_lines, current_section_at_start, current_section_type_at_start))
            current_number = number
            current_lines = []
            current_section_at_start = current_section
            current_section_type_at_start = current_section_type
            body = (question_match.group("body") or "").strip()
            if body:
                current_lines.append(body)
            expected_number += 1
            continue

        if current_lines is not None:
            # Parenthesized subquestions, circled answer steps, tables and
            # ordinary paragraphs all remain in the current top-level block.
            current_lines.append(line)

    if not saw_top_level or current_lines is None or current_number is None:
        return None
    blocks.append((current_number, current_lines, current_section_at_start, current_section_type_at_start))

    valid: list[dict[str, Any]] = []
    for number, body_lines, section_title, section_type in blocks:
        item, error = _rule_question_from_block(
            number=number,
            body_lines=body_lines,
            section_title=section_title,
            section_type=section_type,
        )
        if item is None:
            warnings.append(f"第 {number} 题格式不完整：{error}。")
        else:
            valid.append(item)

    # A document with no complete rule-shaped questions is still a candidate
    # for the AI fallback (for example an OCR text export without answers).
    # Once at least one complete block exists, however, keep the deterministic
    # partial result instead of letting AI invent replacements for the others.
    if not valid:
        return None

    is_complete = not sequence_error and len(valid) == len(blocks)
    if not is_complete:
        warnings.append("规则解析结果不完整，当前预览不能确认导入。")
    return valid, warnings, {
        "chunk_ms": elapsed_ms(start),
        "ai_ms": 0,
        "total_ms": elapsed_ms(start),
        "chunks": 1,
        "ai_chunks": [],
        "completed_chunks": 1 if is_complete else 0,
        "failed_chunks": 0 if is_complete else 1,
        "batches": 1,
        "is_complete": is_complete,
        "rule_based": True,
        "source_questions": len(blocks),
    }


def _extract_pdf(path: str, warnings: list[str]) -> tuple[str, list[str]]:
    from pypdf import PdfReader

    try:
        reader = PdfReader(path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"PDF 文件读取失败：{exc}") from exc

    if reader.is_encrypted:
        try:
            if reader.decrypt("") == 0:
                raise HTTPException(status_code=400, detail="PDF 文件已加密，请先解除密码后再上传。")
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail="PDF 文件已加密，请先解除密码后再上传。") from exc

    parts: list[str] = []
    for page_index, page in enumerate(reader.pages, start=1):
        try:
            text = (page.extract_text() or "").strip()
        except Exception as exc:
            warnings.append(f"第 {page_index} 页 PDF 文本提取失败：{exc}")
            continue
        if text:
            parts.append(f"[Page {page_index}]\n{text}")

    return "\n\n".join(parts), warnings


def _extract_pptx(path: str, warnings: list[str]) -> tuple[str, list[str]]:
    from pptx import Presentation

    prs = Presentation(path)
    parts: list[str] = []

    for slide_index, slide in enumerate(prs.slides, start=1):
        slide_parts: list[str] = []
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                slide_parts.append(shape.text.strip())
            if shape.has_table:
                for row in shape.table.rows:
                    row_texts = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_texts:
                        slide_parts.append(" | ".join(row_texts))
        if slide_parts:
            parts.append(f"[Slide {slide_index}]\n" + "\n".join(slide_parts))

    return "\n".join(parts), warnings


def extract_text_from_file(file_path: str) -> str:
    text, _ = extract_text_and_warnings(file_path)
    return text


def _extract_text_or_raise_legacy(file_path: str) -> tuple[str, list[str]]:
    try:
        text, warnings = extract_text_and_warnings(file_path)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="文件提取失败，请检查文件格式") from exc

    if not text.strip():
        raise HTTPException(status_code=400, detail="文档中未提取到任何文本内容")
    return text, warnings


def extract_text_or_raise(file_path: str) -> tuple[str, list[str]]:
    try:
        text, warnings = extract_text_and_warnings(file_path)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="文件提取失败，请检查文件格式") from exc

    if text.strip():
        return text, warnings

    images, image_warnings = extract_images_from_file(file_path)
    warnings.extend(image_warnings)
    ext = Path(file_path).suffix.lower()
    if images:
        return text, warnings
    if ext == ".pptx":
        raise HTTPException(status_code=400, detail="未从 PPT 中识别到文字或图片题目，请检查文件是否为空，或尝试导出为图片后上传。")
    if ext == ".pdf":
        raise HTTPException(status_code=400, detail="未从 PDF 中提取到文字，请确认不是扫描版图片 PDF，或将页面导出为图片后上传。")
    raise HTTPException(status_code=400, detail="文档中未提取到任何文本内容")


def build_ai_prompt(text_chunk: str, expected_question_count: int = 0) -> str:
    coverage_rule = ""
    if expected_question_count:
        coverage_rule = (
            f"This chunk contains exactly {expected_question_count} numbered question blocks. "
            f"Return exactly {expected_question_count} question objects, one for every numbered block.\n"
        )
    return (
        "You are an exam-question extraction assistant. Convert the document text into strict JSON.\n"
        "Extract EVERY complete question in this chunk. Do not summarize. Do not return only one sample.\n"
        "If the chunk contains 12 complete questions, return 12 question objects. Preserve numbered questions.\n"
        + coverage_rule
        + "If there are no complete questions in this chunk, return {\"questions\": []}.\n"
        "Return ONLY a JSON object with this shape:\n"
        "{\n"
        '  "questions": [\n'
        "    {\n"
        '      "type": "single_choice | multiple_choice | true_false | fill_blank | short_answer",\n'
        '      "question": "question text",\n'
        '      "options": {"A": "option A", "B": "option B"},\n'
        '      "answer": "correct answer",\n'
        '      "analysis": "short explanation",\n'
        '      "subject": "subject name",\n'
        '      "chapter": "chapter name",\n'
        '      "difficulty": "easy | normal | hard"\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Rules:\n"
        "1. Use the original language of the document for question text and analysis.\n"
        "2. For choice questions, options must be an object keyed by A/B/C/D.\n"
        "3. For true_false answers, use one of: true, false, yes, no.\n"
        "4. Split combined numbered lists into separate question objects.\n"
        "5. Do not include markdown fences or explanations outside JSON.\n\n"
        f"Document text:\n{text_chunk}"
    )


def build_ai_multimodal_prompt(text: str = "") -> str:
    context = text.strip() or "(no extracted text; identify questions from the images)"
    return (
        "You are an exam-question extraction assistant. Extract all exam questions from the text and images.\n"
        "Return ONLY strict JSON, with no markdown or explanation. Shape:\n"
        '{"questions":[{"type":"single_choice | multiple_choice | true_false | fill_blank | short_answer",'
        '"question":"question text","options":{"A":"option A","B":"option B"},'
        '"answer":"correct answer","analysis":"short explanation","subject":"",'
        '"chapter":"","difficulty":"normal"}]}\n'
        "Rules: single_choice answer like A; multiple_choice answer like A,B; true_false answer uses "
        "正确 or 错误; extract every question from every image; skip uncertain decorative text.\n\n"
        f"Extracted document text:\n{context}"
    )


def build_ai_image_text_prompt() -> str:
    return (
        "Identify the exam-question text in these images. Return plain text only, preserving question stems, "
        "options, answers, and analysis when visible. Do not describe decorative elements."
    )


def build_ai_repair_prompt(raw_response: str) -> str:
    return (
        "The previous assistant response was not valid import JSON. "
        "Convert it into strict JSON now.\n"
        "Return ONLY a JSON object with this shape:\n"
        '{"questions":[{"type":"single_choice | multiple_choice | true_false | fill_blank | short_answer",'
        '"question":"question text","options":{"A":"option A","B":"option B"},'
        '"answer":"correct answer","analysis":"short explanation","subject":"subject name",'
        '"chapter":"chapter name","difficulty":"easy | normal | hard"}]}\n'
        'If the text contains no question, return {"questions":[]}.\n\n'
        f"Previous response:\n{raw_response}"
    )


def _text_field(value: Any, default: str = "") -> str:
    """Return a safe text field from untrusted AI JSON."""
    return value.strip() if isinstance(value, str) else default


def validate_question_item(item: Any) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(item, dict):
        return None, "题目记录不是对象"

    q_type = _text_field(item.get("type"))
    question = _text_field(item.get("question"))
    answer = _text_field(item.get("answer"))

    if q_type not in VALID_QUESTION_TYPES:
        return None, f"无效的题目类型 '{q_type}'"
    if not question:
        return None, "题目题干不能为空"
    if not answer:
        return None, "题目答案不能为空"
    if q_type in ("single_choice", "multiple_choice"):
        options = item.get("options")
        if not options or not isinstance(options, dict) or len(options) < 2:
            return None, f"选择题（{q_type}）必须至少提供两个选项"

    # Normalize optional fields before building the persisted record. Model
    # output is untrusted JSON, so optional values can be arrays or objects.
    item = {
        **item,
        "analysis": _text_field(item.get("analysis")),
        "subject": _text_field(item.get("subject"), "默认科目"),
        "chapter": _text_field(item.get("chapter"), "默认章节"),
        "difficulty": _text_field(item.get("difficulty"), "normal"),
    }

    return {
        "type": q_type,
        "question": question,
        "options": item.get("options"),
        "answer": normalize_answer(answer, q_type),
        "analysis": (item.get("analysis") or "").strip(),
        "subject": (item.get("subject") or "默认科目").strip(),
        "chapter": (item.get("chapter") or "默认章节").strip(),
        "difficulty": (item.get("difficulty") or "normal").strip(),
    }, None


def question_items_from_parsed_json(parsed: Any) -> list[dict[str, Any]]:
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        items = parsed.get("questions") or parsed.get("items") or parsed.get("data") or parsed.get("result") or []
        if isinstance(items, dict):
            items = items.get("questions") or items.get("items") or items.get("result") or []
        if not items and parsed and ("question" in parsed or "type" in parsed):
            return [parsed]
        return items if isinstance(items, list) else []
    return []


def json_candidates_from_text(raw: str) -> list[str]:
    text = (raw or "").strip()
    candidates: list[str] = []
    if not text:
        return candidates

    candidates.append(text)

    for match in re.finditer(r"```(?:json|JSON)?\s*([\s\S]*?)```", text):
        fenced = match.group(1).strip()
        if fenced:
            candidates.append(fenced)

    for open_char, close_char in (("{", "}"), ("[", "]")):
        start = text.find(open_char)
        while start != -1:
            depth = 0
            in_string = False
            escaped = False
            for idx in range(start, len(text)):
                ch = text[idx]
                if in_string:
                    if escaped:
                        escaped = False
                    elif ch == "\\":
                        escaped = True
                    elif ch == '"':
                        in_string = False
                    continue
                if ch == '"':
                    in_string = True
                elif ch == open_char:
                    depth += 1
                elif ch == close_char:
                    depth -= 1
                    if depth == 0:
                        candidates.append(text[start : idx + 1].strip())
                        break
            start = text.find(open_char, start + 1)

    unique: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        if item and item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


def extract_questions_from_ai_response(raw: str) -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    last_error = ""

    for candidate in json_candidates_from_text(raw):
        try:
            parsed = json_module.loads(candidate)
            if isinstance(parsed, str):
                parsed = json_module.loads(parsed)
        except json_module.JSONDecodeError as exc:
            last_error = str(exc)
            continue

        items = question_items_from_parsed_json(parsed)
        if items:
            if candidate.strip() != (raw or "").strip():
                warnings.append("AI 返回内容包含说明文字，已自动提取其中的 JSON")
            return items, warnings

    if last_error:
        warnings.append(f"AI 返回了非 JSON 格式内容，已忽略此分块（{last_error}）")
    else:
        warnings.append("AI 返回内容中未找到 questions 数组，已忽略此分块")
    return [], warnings


def _build_import_client():
    """Return the OpenAI client to use for import parsing.

    Existing tests inject a fake ``OpenAI`` class via ``sync_ai_settings``;
    when that override is active we honor it (instantiating the injected
    class per-call, as before) so mocks keep working. In production there
    is no override, so we reuse the singleton import client from
    ``ai_client`` to avoid rebuilding the httpx connection pool each call.
    """
    if _ai_override_active():
        return OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL,
            timeout=IMPORT_UPSTREAM_TIMEOUT,
        )
    from ..services.ai_client import get_import_client

    return get_import_client()


def safe_ai_error_detail(exc: Exception | None = None) -> str:
    """Return a user-safe upstream AI error message.

    Provider exceptions can include request ids, upstream internals, or even
    credential fragments. Keep API responses useful without leaking details.
    """
    if isinstance(exc, APIStatusError):
        if exc.status_code in (401, 403):
            return "AI 服务鉴权失败，请检查后端 AI Key 和接口地址配置"
        if exc.status_code == 429:
            return "AI 服务请求过于频繁，请稍后重试"
    if isinstance(exc, APIConnectionError):
        return "AI 服务连接失败，请检查网络或接口地址后重试"
    return "AI 服务暂时不可用，请稍后重试"


def _ensure_openai_key() -> None:
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=400,
            detail="未配置 OPENAI_API_KEY，请在 .env 文件中设置 OPENAI_API_KEY 以使用 AI 自动导入功能",
        )


def _multimodal_content(prompt: str, images: list[ImagePayload]) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    for image in images:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": image_bytes_to_data_url(image.data, image.mime_type)},
            }
        )
    return content


def _call_chat_completion(content: str | list[dict[str, Any]], *, temperature: float = 0.1):
    client = _build_import_client()
    try:
        return client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": content}],
            response_format={"type": "json_object"},
            temperature=temperature,
            max_tokens=AI_MAX_TOKENS,
        )
    except APITimeoutError as exc:
        raise HTTPException(status_code=504, detail="AI 调用超时，请稍后重试") from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail="AI 调用超时，请稍后重试") from exc
    except HTTPException:
        raise
    except (APIStatusError, APIConnectionError) as exc:
        raise HTTPException(status_code=502, detail=safe_ai_error_detail(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=safe_ai_error_detail(exc)) from exc


def _validate_ai_items(items: list[dict[str, Any]], warnings: list[str]) -> list[dict[str, Any]]:
    valid: list[dict[str, Any]] = []
    for index, item in enumerate(deduplicate_questions(items)):
        validated, error = validate_question_item(item)
        if validated:
            validated["line_number"] = index + 1
            valid.append(validated)
        else:
            warnings.append(f"第 {index + 1} 题格式有误: {error}")
    return valid


def call_ai_parse_multimodal(
    text: str,
    images: list[ImagePayload],
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    _ensure_openai_key()
    total_start = time.perf_counter()
    ai_start = time.perf_counter()
    response = _call_chat_completion(_multimodal_content(build_ai_multimodal_prompt(text), images))
    ai_ms = elapsed_ms(ai_start)
    raw = response.choices[0].message.content if response.choices else ""
    if not raw:
        timing = {"chunk_ms": 0, "ai_ms": ai_ms, "chunks": 1, "ai_chunks": [ai_ms], "total_ms": elapsed_ms(total_start)}
        return [], ["AI 返回了空响应"], timing

    items, warnings = extract_questions_from_ai_response(raw)
    valid = _validate_ai_items(items, warnings)
    timing = {"chunk_ms": 0, "ai_ms": ai_ms, "chunks": 1, "ai_chunks": [ai_ms], "total_ms": elapsed_ms(total_start)}
    if not valid:
        ensure_questions_found(valid, warnings)
    return valid, warnings, timing


def call_ai_extract_text_from_images(images: list[ImagePayload]) -> tuple[str, list[str], dict[str, Any]]:
    _ensure_openai_key()
    total_start = time.perf_counter()
    ai_start = time.perf_counter()
    client = _build_import_client()
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": _multimodal_content(build_ai_image_text_prompt(), images)}],
            temperature=0.1,
            max_tokens=AI_MAX_TOKENS,
        )
    except APITimeoutError as exc:
        raise HTTPException(status_code=504, detail="AI 调用超时，请稍后重试") from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail="AI 调用超时，请稍后重试") from exc
    except HTTPException:
        raise
    except (APIStatusError, APIConnectionError) as exc:
        raise HTTPException(status_code=502, detail=safe_ai_error_detail(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=safe_ai_error_detail(exc)) from exc

    ai_ms = elapsed_ms(ai_start)
    text = response.choices[0].message.content if response.choices else ""
    timing = {"chunk_ms": 0, "ai_ms": ai_ms, "chunks": 1, "ai_chunks": [ai_ms], "total_ms": elapsed_ms(total_start)}
    if not text.strip():
        return "", ["图片识别失败：AI 返回了空响应"], timing
    return text.strip(), [], timing


def call_ai_parse_chunk(
    text_chunk: str,
    chunk_index: int,
    expected_question_count: int = 0,
) -> tuple[list[dict[str, Any]], list[str]]:
    client = _build_import_client()
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": build_ai_prompt(text_chunk, expected_question_count),
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=AI_MAX_TOKENS,
        )
    except APITimeoutError as exc:
        raise HTTPException(status_code=504, detail="AI 调用超时，请稍后重试") from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail="AI 调用超时，请稍后重试") from exc
    except HTTPException:
        raise
    except (APIStatusError, APIConnectionError) as exc:
        raise HTTPException(status_code=502, detail=safe_ai_error_detail(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=safe_ai_error_detail(exc)) from exc

    raw = response.choices[0].message.content if response.choices else ""
    if not raw:
        return [], [f"第 {chunk_index + 1} 部分 AI 返回了空响应"]

    items, warnings = extract_questions_from_ai_response(raw)
    should_repair = not items and raw.strip() and '"questions"' not in raw and '"question"' not in raw
    if should_repair:
        try:
            repair_response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": build_ai_repair_prompt(raw)}],
                response_format={"type": "json_object"},
                temperature=0,
                max_tokens=AI_MAX_TOKENS,
            )
            repair_raw = repair_response.choices[0].message.content if repair_response.choices else ""
            repaired_items, repair_warnings = extract_questions_from_ai_response(repair_raw)
            if repaired_items:
                items = repaired_items
                warnings = ["AI 返回格式异常，已自动尝试修复为 JSON"] + repair_warnings
        except (APITimeoutError, TimeoutError):
            warnings.append("AI 返回格式异常，自动修复请求超时")
        except Exception:
            warnings.append("AI 返回格式异常，自动修复失败")

    if warnings:
        warnings = [f"第 {chunk_index + 1} 部分: {warning}" for warning in warnings]
    return items, warnings


def deduplicate_questions(questions: list[Any]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for item in questions:
        # Valid JSON can still contain a scalar or a nested list. Ignore that
        # record instead of letting AttributeError abort the entire task.
        if not isinstance(item, dict):
            continue
        question = item.get("question")
        # Keep malformed objects for validation below, so the user receives a
        # useful incomplete-preview warning instead of silently losing data.
        if not isinstance(question, str):
            result.append(item)
            continue
        key = question.strip()[:100]
        if key and key not in seen:
            seen.add(key)
            result.append(item)
    return result


def count_numbered_question_blocks(text: str) -> int:
    """Return the number of numbered question starts in a text fragment."""
    return len(list(_NUMBERED_QUESTION_BOUNDARY.finditer(text or "")))


def split_numbered_question_blocks(text: str) -> list[str]:
    """Split a document into complete numbered-question blocks when possible."""
    boundaries = list(_NUMBERED_QUESTION_BOUNDARY.finditer(text or ""))
    if len(boundaries) < 2:
        return []

    prefix = text[: boundaries[0].start()].strip()
    blocks = [
        text[match.start() : next_match.start()].strip()
        for match, next_match in zip(boundaries, boundaries[1:], strict=False)
    ]
    blocks.append(text[boundaries[-1].start() :].strip())
    if prefix and blocks:
        blocks[0] = f"{prefix}\n{blocks[0]}"
    return [block for block in blocks if block]


def split_text_unit_for_size(unit: str) -> list[str]:
    """Split one oversized unit without breaking the normal paragraph path."""
    remaining = unit.strip()
    pieces: list[str] = []
    while len(remaining) > AI_CHUNK_SIZE:
        window = remaining[: AI_CHUNK_SIZE + 1]
        split_at = max(window.rfind(mark) for mark in ("。", "！", "？", "；", ";", "，", ",", " "))
        if split_at < max(1, AI_CHUNK_SIZE // 2):
            split_at = AI_CHUNK_SIZE
        else:
            split_at += 1
        pieces.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    if remaining:
        pieces.append(remaining)
    return pieces


def pack_question_blocks(question_blocks: list[str], *, max_questions: int) -> list[str]:
    """Pack complete numbered questions with both size and count limits."""
    chunks: list[str] = []
    current_parts: list[str] = []
    current_size = 0
    current_question_count = 0

    def flush() -> None:
        nonlocal current_parts, current_size, current_question_count
        if current_parts:
            chunks.append("\n".join(current_parts))
        current_parts = []
        current_size = 0
        current_question_count = 0

    for question_block in question_blocks:
        pieces = split_text_unit_for_size(question_block)
        for piece_index, piece in enumerate(pieces):
            starts_question = piece_index == 0
            would_exceed_size = current_parts and current_size + len(piece) + 1 > AI_CHUNK_SIZE
            would_exceed_count = starts_question and current_question_count >= max_questions
            if would_exceed_size or would_exceed_count:
                flush()
            current_parts.append(piece)
            current_size += len(piece) + (1 if current_size else 0)
            if starts_question:
                current_question_count += 1
    flush()
    return chunks


def chunk_document_text(text: str) -> tuple[list[str], int]:
    chunk_start = time.perf_counter()
    question_blocks = split_numbered_question_blocks(text)
    if question_blocks:
        return (
            pack_question_blocks(question_blocks, max_questions=MAX_NUMBERED_QUESTIONS_PER_CHUNK),
            elapsed_ms(chunk_start),
        )

    paragraphs = [paragraph.strip() for paragraph in text.split("\n") if paragraph.strip()]
    units = [piece for paragraph in paragraphs for piece in split_text_unit_for_size(paragraph)]
    chunks: list[str] = []
    current = ""
    for unit in units:
        if len(current) + len(unit) + 1 > AI_CHUNK_SIZE:
            if current:
                chunks.append(current)
            current = unit
        else:
            current = current + "\n" + unit if current else unit
    if current:
        chunks.append(current)
    return chunks, elapsed_ms(chunk_start)


def parse_chunk_with_coverage_retry(
    text_chunk: str,
    chunk_index: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Retry an incomplete numbered chunk in smaller batches before importing it."""
    expected_question_count = count_numbered_question_blocks(text_chunk)
    items, warnings = call_ai_parse_chunk(text_chunk, chunk_index, expected_question_count)
    if expected_question_count < 2 or len(items) >= expected_question_count:
        return items, warnings

    question_blocks = split_numbered_question_blocks(text_chunk)
    retry_chunks = pack_question_blocks(
        question_blocks,
        max_questions=RETRY_NUMBERED_QUESTIONS_PER_CHUNK,
    )
    if len(retry_chunks) <= 1:
        warnings.append(
            f"第 {chunk_index + 1} 部分检测到约 {expected_question_count} 道编号题，"
            f"AI 仅返回 {len(items)} 道，请重新解析后再确认导入。"
        )
        return items, warnings

    retry_items: list[dict[str, Any]] = []
    retry_warnings: list[str] = []
    for retry_chunk in retry_chunks:
        expected_retry_count = count_numbered_question_blocks(retry_chunk)
        parsed_items, parsed_warnings = call_ai_parse_chunk(
            retry_chunk,
            chunk_index,
            expected_retry_count,
        )
        retry_items.extend(parsed_items)
        retry_warnings.extend(parsed_warnings)

    retry_items = deduplicate_questions(retry_items)
    if len(retry_items) > len(items):
        items = retry_items
    warnings.extend(retry_warnings)
    if len(items) >= expected_question_count:
        warnings.append(f"第 {chunk_index + 1} 部分初次返回不完整，已自动拆分重试并补全题目。")
    else:
        warnings.append(
            f"第 {chunk_index + 1} 部分检测到约 {expected_question_count} 道编号题，"
            f"自动拆分重试后仍仅返回 {len(items)} 道，请重新解析后再确认导入。"
        )
    return items, warnings


def parse_chunk_with_transient_retry(
    text_chunk: str,
    chunk_index: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Retry only transient upstream failures; malformed input is not retried."""
    for attempt in range(AI_CHUNK_MAX_ATTEMPTS):
        try:
            return parse_chunk_with_coverage_retry(text_chunk, chunk_index)
        except HTTPException as exc:
            if exc.status_code not in {502, 504} or attempt + 1 >= AI_CHUNK_MAX_ATTEMPTS:
                raise
    raise AssertionError("unreachable")


def _validated_question_snapshot(items: list[Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """Return only persistable questions plus safe validation warnings."""
    valid: list[dict[str, Any]] = []
    warnings: list[str] = []
    for index, item in enumerate(deduplicate_questions(items), start=1):
        validated, error = validate_question_item(item)
        if validated:
            validated["line_number"] = index
            valid.append(validated)
        else:
            warnings.append(f"第 {index} 题格式有误: {error}")
    return valid, warnings


def call_ai_parse(
    text: str,
    *,
    on_progress: ParseProgressCallback | None = None,
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    total_start = time.perf_counter()
    timing = {
        "chunk_ms": 0,
        "ai_ms": 0,
        "total_ms": 0,
        "chunks": 0,
        "ai_chunks": [],
        "completed_chunks": 0,
        "failed_chunks": 0,
        "batches": 0,
        "is_complete": True,
    }
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=400,
            detail="未配置 OPENAI_API_KEY，请在 .env 文件中设置 OPENAI_API_KEY 以使用 AI 自动导入功能",
        )

    all_items: list[dict[str, Any]] = []
    all_warnings: list[str] = []
    chunks, timing["chunk_ms"] = chunk_document_text(text)

    timing["chunks"] = len(chunks)
    expected_numbered_questions = sum(count_numbered_question_blocks(chunk) for chunk in chunks)

    if on_progress is not None:
        on_progress([], [], timing.copy())

    saw_timeout = False
    saw_invalid_json = False
    saw_upstream_error = False
    other_http_error: HTTPException | None = None

    for batch_start in range(0, len(chunks), AI_BATCH_SIZE):
        # Batches are intentionally sequential.  This protects the upstream
        # service while every document chunk is still processed in order.
        timing["batches"] += 1
        for index, chunk in enumerate(chunks[batch_start : batch_start + AI_BATCH_SIZE], start=batch_start):
            ai_start = time.perf_counter()
            try:
                items, warnings = parse_chunk_with_transient_retry(chunk, index)
                all_items.extend(items)
                all_warnings.extend(warnings)
                timing["completed_chunks"] += 1
                if any("非 JSON" in warning for warning in warnings):
                    saw_invalid_json = True
            except HTTPException as exc:
                timing["failed_chunks"] += 1
                timing["is_complete"] = False
                if exc.status_code == 504:
                    saw_timeout = True
                elif exc.status_code == 502:
                    saw_upstream_error = True
                elif exc.status_code != 400:
                    other_http_error = exc
                all_warnings.append(f"第 {index + 1} 部分解析失败: {exc.detail}")
            finally:
                ai_chunk_ms = elapsed_ms(ai_start)
                timing["ai_chunks"].append(ai_chunk_ms)
                timing["ai_ms"] += ai_chunk_ms
                timing["total_ms"] = elapsed_ms(total_start)
                if on_progress is not None:
                    snapshot_questions, snapshot_warnings = _validated_question_snapshot(all_items)
                    on_progress(snapshot_questions, all_warnings + snapshot_warnings, timing.copy())

    malformed_item_count = sum(1 for item in all_items if not isinstance(item, dict))
    if malformed_item_count:
        timing["is_complete"] = False
        all_warnings.append(f"AI 返回了 {malformed_item_count} 条无效题目记录，已跳过；当前结果不能确认导入。")
    all_items = deduplicate_questions(all_items)

    valid, validation_warnings = _validated_question_snapshot(all_items)
    all_warnings.extend(validation_warnings)

    invalid_item_count = len(all_items) - len(valid)
    if invalid_item_count:
        timing["is_complete"] = False
        all_warnings.append(f"AI 返回 {invalid_item_count} 条字段格式异常的题目，当前结果不能确认导入。")

    timing["total_ms"] = elapsed_ms(total_start)

    if (
        expected_numbered_questions >= MAX_NUMBERED_QUESTIONS_PER_CHUNK
        and len(valid) / expected_numbered_questions < MIN_NUMBERED_QUESTION_COVERAGE_RATIO
    ):
        timing["is_complete"] = False
        all_warnings.append(
            f"AI 解析不完整：检测到约 {expected_numbered_questions} 道编号题，"
            f"当前仅解析到 {len(valid)} 道。已保留可预览结果，但不能确认导入。"
        )

    if not valid and other_http_error:
        raise other_http_error
    if not valid and saw_timeout:
        raise HTTPException(status_code=504, detail="AI 调用超时，请稍后重试")
    if not valid and saw_upstream_error:
        raise HTTPException(status_code=502, detail=safe_ai_error_detail())
    if not valid and saw_invalid_json:
        raise HTTPException(status_code=400, detail="AI 未能解析出题目，请换一个文件或稍后重试。")

    return valid, all_warnings, timing


def ensure_questions_found(questions: list[dict[str, Any]], warnings: list[str]) -> None:
    if questions:
        return
    detail = "未能从文档中解析出任何有效题目"
    if warnings:
        detail += "（" + "；".join(warnings[:3]) + "）"
    raise HTTPException(status_code=400, detail=detail)


def preview_import_from_text(text: str) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    rule_result = parse_rule_based_question_document(text)
    if rule_result is not None:
        questions, warnings, timing = rule_result
    else:
        questions, warnings, timing = call_ai_parse(text)
    ensure_questions_found(questions, warnings)
    return questions, warnings, timing


def preview_import_from_file_content(
    text: str,
    images: list[ImagePayload],
    *,
    on_text_progress: ParseProgressCallback | None = None,
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    all_questions: list[dict[str, Any]] = []
    all_warnings: list[str] = []
    timings: list[dict[str, Any]] = []
    failures: list[HTTPException] = []
    used_rule_parser = False

    # Text is the most complete source for Word/PDF/PPT exports. Parse it first
    # so embedded logos or screenshots cannot collapse a long document into one
    # multimodal request with a truncated answer.
    if text.strip():
        try:
            rule_result = parse_rule_based_question_document(text)
            used_rule_parser = rule_result is not None
            if rule_result is not None:
                questions, warnings, timing = rule_result
                if on_text_progress is not None:
                    on_text_progress(questions, warnings, timing.copy())
            elif on_text_progress is None:
                questions, warnings, timing = call_ai_parse(text)
            else:
                questions, warnings, timing = call_ai_parse(text, on_progress=on_text_progress)
            all_questions.extend(questions)
            all_warnings.extend(warnings)
            timings.append(timing)
        except HTTPException as exc:
            failures.append(exc)
            all_warnings.append(f"文本解析失败：{exc.detail}")

    if used_rule_parser and images:
        # Re-parsing a regular text document through the image model creates
        # detached duplicates. A question that explicitly needs a diagram must
        # remain partial until question-image storage is available.
        if re.search(r"(?:如下图|下图|见图|如图)", text):
            all_warnings.append("题目引用了文档图片，但当前题库数据模型尚不能关联题图；为避免导入缺图题目，已禁止确认导入。")
            if timings:
                timings[0]["is_complete"] = False
                timings[0]["failed_chunks"] = max(1, int(timings[0].get("failed_chunks") or 0))
                timings[0]["completed_chunks"] = 0
        else:
            all_warnings.append("已跳过内嵌图片的独立 AI 识别，避免与规则解析出的题目重复。")

    # Keep image recognition available, but bound each request. A document can
    # contain up to 12 images; one oversized multimodal request is both slower
    # and more likely to return only a sample of the questions.
    for index in range(0, len(images), AI_IMAGE_BATCH_SIZE):
        if used_rule_parser:
            break
        batch = images[index : index + AI_IMAGE_BATCH_SIZE]
        try:
            questions, warnings, timing = call_ai_parse_multimodal("", batch)
            all_questions.extend(questions)
            all_warnings.extend(warnings)
            timings.append(timing)
        except HTTPException as exc:
            failures.append(exc)
            all_warnings.append(f"第 {index // AI_IMAGE_BATCH_SIZE + 1} 组图片解析失败：{exc.detail}")

    all_questions = deduplicate_questions(all_questions)
    if all_questions:
        return all_questions, all_warnings, {
            "chunk_ms": sum(int(item.get("chunk_ms") or 0) for item in timings),
            "ai_ms": sum(int(item.get("ai_ms") or 0) for item in timings),
            "total_ms": sum(int(item.get("total_ms") or 0) for item in timings),
            "chunks": sum(int(item.get("chunks") or 0) for item in timings),
            "ai_chunks": [duration for item in timings for duration in item.get("ai_chunks") or []],
            "completed_chunks": sum(int(item.get("completed_chunks") or 0) for item in timings),
            "failed_chunks": sum(int(item.get("failed_chunks") or 0) for item in timings),
            "batches": sum(int(item.get("batches") or 0) for item in timings),
            "is_complete": all(bool(item.get("is_complete", True)) for item in timings),
        }

    if failures:
        raise failures[0]
    ensure_questions_found(all_questions, all_warnings)
    return all_questions, all_warnings, {"chunk_ms": 0, "ai_ms": 0, "total_ms": 0, "chunks": 0, "ai_chunks": []}


def validate_imported_questions(
    questions: list[schemas.ImportedQuestion],
) -> tuple[list[schemas.ImportedQuestion], list[str]]:
    errors: list[str] = []
    validated_items: list[schemas.ImportedQuestion] = []
    for index, question in enumerate(questions):
        validated, error = validate_question_item(question.model_dump())
        if error:
            errors.append(f"第 {index + 1} 题: {error}")
        else:
            validated_items.append(schemas.ImportedQuestion(**validated))
    return validated_items, errors


def resolve_target_course(
    db: Session,
    user_id: int,
    *,
    course_id: int = 0,
    course_name: str = "",
    filename: str = "",
    commit: bool = True,
):
    try:
        if course_id > 0:
            bank, _ = crud.resolve_course(db, user_id, course_id=course_id, commit=commit)
        elif course_name.strip():
            bank, _ = crud.resolve_course(db, user_id, course_name=course_name.strip(), commit=commit)
        else:
            derived = derive_course_name_from_filename(filename)
            bank, _ = crud.resolve_course(db, user_id, course_name=derived, commit=commit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return bank


def persist_imported_questions(
    db: Session,
    *,
    user_id: int,
    course_id: int,
    questions: list[schemas.ImportedQuestion | dict[str, Any]],
    commit: bool = True,
) -> int:
    now = datetime.now(UTC)
    models_to_add: list[QuestionModel] = []
    for question_data in questions:
        data = question_data.model_dump() if hasattr(question_data, "model_dump") else question_data
        question = QuestionModel(
            owner_id=user_id,
            course_id=course_id,
            visibility="private",
            source="import",
            created_at=now,
            subject=data["subject"],
            chapter=data["chapter"],
            type=data["type"],
            question=data["question"],
            answer=normalize_answer(data["answer"], data["type"]),
            analysis=data.get("analysis", ""),
            difficulty=data.get("difficulty", "normal"),
        )
        question.set_options_dict(data.get("options"))
        models_to_add.append(question)

    try:
        db.add_all(models_to_add)
        if commit:
            db.commit()
        else:
            db.flush()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="导入失败，已回滚") from exc
    return len(models_to_add)
