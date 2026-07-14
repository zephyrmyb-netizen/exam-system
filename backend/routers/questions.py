from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import auth as auth_module
from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/questions", tags=["questions"])


def _get_owned_question(db: Session, question_id: int, user_id: int):
    """Return a question if it exists and the current user owns it."""
    question = crud.get_question_by_id(db, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    if question.owner_id is None or question.owner_id != user_id:
        raise HTTPException(status_code=403, detail="只能操作自己的题目")
    return question


@router.post("/batch")
def batch_import(
    questions: list[schemas.QuestionCreate],
    course_id: int = Query(0, ge=0, description="目标课程ID（0表示使用 course_name 或自动处理）"),
    course_name: str = Query("", description="目标课程名（course_id=0 时生效；创建或复用同名题库）"),
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    try:
        # Priority: course_id > course_name > per-question course_id > 未分类题库
        has_any_course = any(q.course_id is not None for q in questions)

        if course_id > 0:
            bank, _ = crud.resolve_course(db, current_user.id, course_id=course_id)
            batch_course_id = bank.id
        elif course_name.strip():
            bank, _ = crud.resolve_course(db, current_user.id, course_name=course_name.strip())
            batch_course_id = bank.id
        elif has_any_course:
            batch_course_id = None  # use per-question course_id
        else:
            bank, _ = crud.resolve_course(db, current_user.id, course_name="未分类题库")
            batch_course_id = bank.id

        count = crud.create_questions_batch(
            db,
            questions,
            owner_id=current_user.id,
            course_id=batch_course_id,
            visibility="private",
            source="import",
        )

        # Determine reported course info
        if batch_course_id is not None:
            reported_course_id = batch_course_id
            bank = crud.get_question_bank_by_id(db, batch_course_id)
            reported_course_name = bank.name if bank else "未分类题库"
        elif has_any_course:
            reported_course_id = questions[0].course_id
            bank = crud.get_question_bank_by_id(db, reported_course_id)
            reported_course_name = bank.name if bank else "未分类题库"
        else:
            reported_course_id = None
            reported_course_name = "未分类题库"

        return schemas.BatchImportResponse(
            imported_count=count,
            course_id=reported_course_id,
            course_name=reported_course_name,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="批量导入失败，请稍后重试") from exc


@router.get("/")
def list_questions(
    page: int = Query(0, ge=0, description="页码（0表示不分页）"),
    page_size: int = Query(0, ge=0, description="每页数量（0表示不分页）"),
    keyword: str = Query("", description="关键词搜索"),
    subject: str = Query("", description="科目筛选"),
    chapter: str = Query("", description="章节筛选"),
    type: str = Query("", alias="type", description="题目类型筛选"),
    course_id: int = Query(0, ge=0, description="课程ID筛选（0表示不筛选）"),
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    try:
        questions, total = crud.get_questions(
            db,
            user_id=current_user.id,
            page=page,
            page_size=page_size,
            keyword=keyword,
            subject=subject,
            chapter=chapter,
            q_type=type,
            course_id=course_id if course_id > 0 else None,
        )
        items = [schemas.QuestionOut.model_validate(q).model_dump() for q in questions]

        if page <= 0 or page_size <= 0:
            return items

        return {"total": total, "page": page, "page_size": page_size, "items": items}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="获取题目列表失败，请稍后重试") from exc


@router.get("/my")
def list_my_questions(
    page: int = Query(0, ge=0, description="页码（0表示不分页）"),
    page_size: int = Query(0, ge=0, description="每页数量（0表示不分页）"),
    keyword: str = Query("", description="关键词搜索"),
    subject: str = Query("", description="科目筛选"),
    chapter: str = Query("", description="章节筛选"),
    type: str = Query("", alias="type", description="题目类型筛选"),
    course_id: int = Query(0, ge=0, description="课程ID筛选（0表示不筛选）"),
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    """List only the current user's own questions (my question pool)."""
    try:
        questions, total = crud.get_my_questions(
            db,
            user_id=current_user.id,
            page=page,
            page_size=page_size,
            keyword=keyword,
            subject=subject,
            chapter=chapter,
            q_type=type,
            course_id=course_id if course_id > 0 else None,
        )
        items = [schemas.QuestionOut.model_validate(q).model_dump() for q in questions]

        if page <= 0 or page_size <= 0:
            return items

        return {"total": total, "page": page, "page_size": page_size, "items": items}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="获取我的题目失败，请稍后重试") from exc


@router.get("/public")
def list_public_questions(
    page: int = Query(0, ge=0, description="页码（0表示不分页）"),
    page_size: int = Query(0, ge=0, description="每页数量（0表示不分页）"),
    keyword: str = Query("", description="关键词搜索"),
    subject: str = Query("", description="科目筛选"),
    chapter: str = Query("", description="章节筛选"),
    type: str = Query("", alias="type", description="题目类型筛选"),
    course_id: int = Query(0, ge=0, description="课程ID筛选（0表示不筛选）"),
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    """List all public questions (the public question pool)."""
    try:
        questions, total = crud.get_public_questions(
            db,
            page=page,
            page_size=page_size,
            keyword=keyword,
            subject=subject,
            chapter=chapter,
            q_type=type,
            course_id=course_id if course_id > 0 else None,
        )
        items = [schemas.QuestionOut.model_validate(q).model_dump() for q in questions]

        if page <= 0 or page_size <= 0:
            return items

        return {"total": total, "page": page, "page_size": page_size, "items": items}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="获取公开题目失败，请稍后重试") from exc


@router.delete("/{question_id}")
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    question = crud.get_question_by_id(db, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")

    # Only the owner can delete their own questions
    if question.owner_id is not None and question.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能删除自己的题目")

    try:
        crud.delete_question(db, question_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="删除题目失败，请稍后重试") from exc
    return {"message": "题目已删除"}


# ── Manual create single question ──────────────────────────────────────────
@router.post("/", status_code=201)
def create_question(
    body: schemas.QuestionManualCreate,
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    """Manually create a single question. Must belong to a course the user owns."""
    # Verify the course belongs to the user
    bank = crud.get_question_bank_by_id(db, body.course_id)
    if not bank:
        raise HTTPException(status_code=404, detail="课程不存在")
    if bank.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能在自己的课程下创建题目")

    try:
        question = crud.create_single_question(db, body, current_user.id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="创建题目失败，请稍后重试") from exc
    return schemas.QuestionOut.model_validate(question).model_dump()


# ── Edit question ──────────────────────────────────────────────────────────
@router.patch("/{question_id}")
def update_question(
    question_id: int,
    body: schemas.QuestionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    """Edit a question's fields. Only the owner can do this."""
    question = _get_owned_question(db, question_id, current_user.id)

    # If changing course_id, verify the target course belongs to the user
    if body.course_id is not None:
        bank = crud.get_question_bank_by_id(db, body.course_id)
        if not bank:
            raise HTTPException(status_code=404, detail="目标课程不存在")
        if bank.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="只能移动到自己的课程")

    # Validate options if type is being changed to a choice type
    new_type = body.type if body.type is not None else question.type
    if new_type in ("single_choice", "multiple_choice"):
        has_options = body.options is not None or question.options is not None
        if not has_options:
            raise HTTPException(status_code=400, detail="选择题必须提供 options")

    try:
        updated = crud.update_question(db, question_id, body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not updated:
        raise HTTPException(status_code=404, detail="题目不存在")
    return schemas.QuestionOut.model_validate(updated).model_dump()


# ── Unpublish question ─────────────────────────────────────────────────────
@router.post("/{question_id}/unpublish")
def unpublish_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    """Unpublish a question (set back to private). Only the owner can do this."""
    question = _get_owned_question(db, question_id, current_user.id)
    if question.visibility == "private":
        raise HTTPException(status_code=400, detail="该题目已为私有")
    try:
        updated = crud.update_question_visibility(db, question_id, "private")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="取消发布失败，请稍后重试") from exc
    return schemas.QuestionOut.model_validate(updated).model_dump()


# ── Publish question ───────────────────────────────────────────────────────
@router.post("/{question_id}/publish")
def publish_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    """Publish a single question to the public question bank.

    Only the owner can publish their own questions.
    """
    question = crud.get_question_by_id(db, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    if question.owner_id is None or question.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能发布自己的题目")
    if question.visibility == "public":
        raise HTTPException(status_code=400, detail="该题目已发布")

    try:
        updated = crud.update_question_visibility(db, question_id, "public")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="发布题目失败，请稍后重试") from exc
    return schemas.QuestionOut.model_validate(updated).model_dump()


@router.get("/meta")
def question_meta(
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    """Get distinct subjects and chapters for filter dropdowns."""
    return crud.get_question_meta(db, user_id=current_user.id)
