"""Public library: browse public courses and their questions."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import auth as auth_module
from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/library", tags=["library"])


@router.get("/public")
def list_public_courses(
    page: int = Query(0, ge=0),
    page_size: int = Query(0, ge=0),
    keyword: str = Query("", description="关键词搜索（匹配课程名、描述、科目）"),
    subject: str = Query("", description="科目筛选"),
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    """Get all public question banks (the public library)."""
    banks, total = crud.get_public_question_banks(
        db, page=page, page_size=page_size, keyword=keyword, subject=subject,
    )
    items = [b.to_dict() for b in banks]
    if page <= 0 or page_size <= 0:
        return items
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.get("/public/{course_id}/questions")
def list_public_course_questions(
    course_id: int,
    page: int = Query(0, ge=0),
    page_size: int = Query(0, ge=0),
    keyword: str = Query("", description="关键词搜索"),
    subject: str = Query("", description="科目筛选"),
    chapter: str = Query("", description="章节筛选"),
    type: str = Query("", alias="type", description="题目类型筛选"),
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    """Get questions from a public course (only public questions are visible)."""
    bank = crud.get_question_bank_by_id(db, course_id)
    if not bank:
        raise HTTPException(status_code=404, detail="课程不存在")
    if bank.visibility != "public":
        raise HTTPException(status_code=404, detail="课程不存在")

    questions, total = crud.get_questions(
        db,
        user_id=current_user.id,
        page=page, page_size=page_size,
        keyword=keyword, subject=subject, chapter=chapter, q_type=type,
        course_id=course_id,
    )
    items = [q.to_dict() for q in questions]

    if page <= 0 or page_size <= 0:
        return items
    return {"total": total, "page": page, "page_size": page_size, "items": items}
