from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import auth as auth_module
from .. import crud, models, schemas
from ..database import get_db

router = APIRouter(prefix="/courses", tags=["courses"])


def _get_accessible_course(db: Session, course_id: int, user_id: int):
    """Return a course if it exists and the user has access (own private or any public)."""
    bank = crud.get_question_bank_by_id(db, course_id)
    if not bank:
        raise HTTPException(status_code=404, detail="课程不存在")
    if bank.visibility == "private" and bank.owner_id != user_id:
        raise HTTPException(status_code=404, detail="课程不存在")
    return bank


def _get_owned_course(db: Session, course_id: int, user_id: int):
    """Return a course if it exists and the current user owns it."""
    bank = crud.get_question_bank_by_id(db, course_id)
    if not bank:
        raise HTTPException(status_code=404, detail="课程不存在")
    if bank.owner_id != user_id:
        raise HTTPException(status_code=403, detail="只能操作自己的课程")
    return bank


@router.post("/", status_code=201)
def create_course(
    body: schemas.CourseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    bank = crud.create_question_bank(db, body, current_user.id)
    return bank


@router.get("/")
def list_courses(
    page: int = Query(0, ge=0),
    page_size: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    banks, total = crud.get_question_banks(db, current_user.id, page=page, page_size=page_size)
    items = [b.to_dict() for b in banks]
    if page <= 0 or page_size <= 0:
        return items
    return {"total": total, "page": page, "page_size": page_size, "items": items}


# ── My courses ──────────────────────────────────────────────────────────────
@router.get("/mine")
def list_my_courses(
    page: int = Query(0, ge=0),
    page_size: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    """Get only the current user's own courses/question banks.

    Each course includes question_count (total questions in the course),
    practice_count (times current user has practiced in this course),
    and last_practiced_at (most recent practice time).
    """
    banks, total = crud.get_my_question_banks(db, current_user.id, page=page, page_size=page_size)

    # Batch-fetch per-course practice stats for the current user
    course_ids = [b.id for b in banks]
    stats_map = crud.get_practice_stats_by_course(db, current_user.id, course_ids)

    items = []
    for b in banks:
        d = b.to_dict()
        # question_count is already in to_dict() via len(b.questions)
        stats = stats_map.get(b.id, {})
        d["practice_count"] = stats.get("practice_count", 0)
        d["last_practiced_at"] = stats.get("last_practiced_at")
        items.append(d)

    if page <= 0 or page_size <= 0:
        return items
    return {"total": total, "page": page, "page_size": page_size, "items": items}


# ── Course detail ───────────────────────────────────────────────────────────
@router.get("/{course_id}")
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    bank = _get_accessible_course(db, course_id, current_user.id)
    return bank.to_dict()


# ── Questions under a course ────────────────────────────────────────────────
@router.get("/{course_id}/questions")
def list_course_questions(
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
    """Get questions under a specific course that the user can see.

    The user must have access to the course (own private or any public).
    Only questions visible to the user (own private + public) are returned.
    """
    _get_accessible_course(db, course_id, current_user.id)

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


# ── Practice from a course ──────────────────────────────────────────────────
@router.get("/{course_id}/practice/random")
def random_question_in_course(
    course_id: int,
    type: str = "",
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    """Get a random question from a specific course (must have access)."""
    _get_accessible_course(db, course_id, current_user.id)

    question = crud.get_random_question_in_course(
        db, course_id, user_id=current_user.id, q_type=type,
    )
    if not question:
        raise HTTPException(status_code=404, detail="该课程下暂无可用题目")
    return question.to_dict()


# ── Publish entire course ───────────────────────────────────────────────────
@router.post("/{course_id}/publish")
def publish_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    """Publish an entire course and all its questions. Only the owner can do this."""
    bank = _get_owned_course(db, course_id, current_user.id)
    if bank.visibility == "public":
        raise HTTPException(status_code=400, detail="该课程已发布")
    crud.update_question_bank_visibility(db, course_id, "public")
    # Also publish all questions in the course (that belong to the user)
    db.query(models.Question).filter(
        models.Question.course_id == course_id,
        models.Question.owner_id == current_user.id,
        models.Question.visibility != "public",
    ).update({"visibility": "public"}, synchronize_session=False)
    db.commit()
    updated = crud.get_question_bank_by_id(db, course_id)
    return updated.to_dict()


# ── Delete course ───────────────────────────────────────────────────────────
@router.delete("/{course_id}")
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    bank = crud.get_question_bank_by_id(db, course_id)
    if not bank:
        raise HTTPException(status_code=404, detail="课程不存在")
    if bank.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能删除自己的课程")
    crud.delete_question_bank(db, course_id)
    return {"message": "课程已删除"}
