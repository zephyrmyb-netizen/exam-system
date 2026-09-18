"""Public library: browse public courses and their questions."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import auth as auth_module
from .. import crud, models, schemas
from ..database import get_db

router = APIRouter(prefix="/library", tags=["library"])


def _get_public_course_or_404(db: Session, course_id: int) -> models.QuestionBank:
    bank = crud.get_question_bank_by_id(db, course_id)
    if bank is None or bank.visibility != "public":
        raise HTTPException(status_code=404, detail="Public course not found")
    return bank


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
        db,
        page=page,
        page_size=page_size,
        keyword=keyword,
        subject=subject,
    )
    items = [schemas.CourseOut.model_validate(b).model_dump() for b in banks]
    if page <= 0 or page_size <= 0:
        return items
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.post("/public/{course_id}/copy", status_code=201, response_model=schemas.PublicCourseActionOut)
def copy_public_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    source = _get_public_course_or_404(db, course_id)
    copied = models.QuestionBank(
        owner_id=current_user.id,
        name=f"{source.name} (copy)",
        description=source.description or "",
        subject=source.subject or "",
        visibility="private",
    )
    db.add(copied)
    db.flush()
    for question in source.questions:
        db.add(
            models.Question(
                owner_id=current_user.id, course_id=copied.id, visibility="private", source="import",
                subject=question.subject, chapter=question.chapter, type=question.type,
                question=question.question, options=question.options, answer=question.answer,
                analysis=question.analysis or "", image_urls=question.image_urls or "[]",
                difficulty=question.difficulty or "normal",
            )
        )
    db.commit()
    return schemas.PublicCourseActionOut(course_id=course_id, copied_course_id=copied.id, message="Course copied")


@router.post("/public/{course_id}/favorite", response_model=schemas.PublicCourseActionOut)
def toggle_public_course_favorite(
    course_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    _get_public_course_or_404(db, course_id)
    favorite = (
        db.query(models.CourseFavorite)
        .filter(models.CourseFavorite.course_id == course_id, models.CourseFavorite.user_id == current_user.id)
        .first()
    )
    if favorite:
        db.delete(favorite)
        db.commit()
        return schemas.PublicCourseActionOut(course_id=course_id, favorited=False, message="Removed from favorites")
    db.add(models.CourseFavorite(course_id=course_id, user_id=current_user.id))
    db.commit()
    return schemas.PublicCourseActionOut(course_id=course_id, favorited=True, message="Added to favorites")


@router.post("/public/{course_id}/report", status_code=201, response_model=schemas.PublicCourseActionOut)
def report_public_course(
    course_id: int,
    body: schemas.CourseReportCreate,
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    _get_public_course_or_404(db, course_id)
    db.add(
        models.CourseReport(
            course_id=course_id, reporter_id=current_user.id,
            reason=body.reason.strip() or "other", detail=body.detail.strip(),
        )
    )
    db.commit()
    return schemas.PublicCourseActionOut(course_id=course_id, message="Report submitted")


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
        page=page,
        page_size=page_size,
        keyword=keyword,
        subject=subject,
        chapter=chapter,
        q_type=type,
        course_id=course_id,
    )
    items = [schemas.QuestionOut.model_validate(q).model_dump() for q in questions]

    if page <= 0 or page_size <= 0:
        return items
    return {"total": total, "page": page, "page_size": page_size, "items": items}
