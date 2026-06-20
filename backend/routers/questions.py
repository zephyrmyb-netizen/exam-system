from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import auth as auth_module
from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/questions", tags=["questions"])


@router.post("/batch")
def batch_import(
    questions: list[schemas.QuestionCreate],
    course_id: int = Query(0, ge=0, description="目标课程ID（0表示使用 course_name 或自动处理）"),
    course_name: str = Query("", description="目标课程名（course_id=0 时生效；创建或复用同名题库）"),
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
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
        db, questions,
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
    questions, total = crud.get_questions(
        db,
        user_id=current_user.id,
        page=page, page_size=page_size,
        keyword=keyword, subject=subject, chapter=chapter, q_type=type,
        course_id=course_id if course_id > 0 else None,
    )
    items = [q.to_dict() for q in questions]

    if page <= 0 or page_size <= 0:
        return items

    return {"total": total, "page": page, "page_size": page_size, "items": items}


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
    questions, total = crud.get_my_questions(
        db,
        user_id=current_user.id,
        page=page, page_size=page_size,
        keyword=keyword, subject=subject, chapter=chapter, q_type=type,
        course_id=course_id if course_id > 0 else None,
    )
    items = [q.to_dict() for q in questions]

    if page <= 0 or page_size <= 0:
        return items

    return {"total": total, "page": page, "page_size": page_size, "items": items}


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
    questions, total = crud.get_public_questions(
        db,
        page=page, page_size=page_size,
        keyword=keyword, subject=subject, chapter=chapter, q_type=type,
        course_id=course_id if course_id > 0 else None,
    )
    items = [q.to_dict() for q in questions]

    if page <= 0 or page_size <= 0:
        return items

    return {"total": total, "page": page, "page_size": page_size, "items": items}


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

    crud.delete_question(db, question_id)
    return {"message": "题目已删除"}


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

    updated = crud.update_question_visibility(db, question_id, "public")
    return updated.to_dict()


@router.get("/meta")
def question_meta(
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    """Get distinct subjects and chapters for filter dropdowns."""
    return crud.get_question_meta(db, user_id=current_user.id)
