"""Admin API for role, platform statistics, and feedback management."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..crud_common import apply_pagination
from ..database import get_db
from .deps import require_permission

router = APIRouter(prefix="/admin", tags=["admin"])

AdminUser = Annotated[models.User, Depends(require_permission("user:manage"))]
StatsUser = Annotated[models.User, Depends(require_permission("stats:view_global"))]


def _admin_user_out(user: models.User) -> schemas.AdminUserOut:
    return schemas.AdminUserOut(id=user.id, username=user.username, role=user.role)


def _admin_feedback_out(entry: models.FeedbackEntry) -> schemas.AdminFeedbackOut:
    return schemas.AdminFeedbackOut(
        id=entry.id,
        user_id=entry.user_id,
        username=entry.user.username,
        display_name=entry.user.display_name or "",
        category=entry.category,
        content=entry.content,
        contact=entry.contact or "",
        status=entry.status,
        admin_reply=entry.admin_reply or "",
        created_at=entry.created_at.isoformat() if entry.created_at else None,
        updated_at=entry.updated_at.isoformat() if entry.updated_at else None,
    )


@router.get("/users", response_model=schemas.AdminUserListOut)
def list_users(
    current_user: AdminUser,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    query = (
        db.query(models.User)
        .options(joinedload(models.User.role_ref))
        .order_by(models.User.id.asc())
    )
    users, total = apply_pagination(query, page, page_size)
    return schemas.AdminUserListOut(
        items=[_admin_user_out(user) for user in users],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch("/users/{user_id}/role", response_model=schemas.AdminUserOut)
def update_user_role(
    user_id: int,
    body: schemas.AdminRoleUpdate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    role_name = body.role.strip()
    if role_name not in {"student", "admin"}:
        raise HTTPException(status_code=400, detail="不支持的角色")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    role = db.query(models.Role).filter(models.Role.name == role_name).first()
    if role is None:
        role = models.Role(name=role_name)
        db.add(role)
        db.commit()
        db.refresh(role)

    user.role_id = role.id
    db.commit()
    db.refresh(user)
    user = db.query(models.User).options(joinedload(models.User.role_ref)).filter(models.User.id == user_id).first()
    return _admin_user_out(user)


@router.get("/stats", response_model=schemas.AdminStatsOut)
def get_admin_stats(
    current_user: StatsUser,
    db: Session = Depends(get_db),
):
    return schemas.AdminStatsOut(
        user_count=db.query(models.User).count(),
        course_count=db.query(models.QuestionBank).count(),
        question_count=db.query(models.Question).count(),
        exam_count=db.query(models.Exam).count(),
        submission_count=db.query(models.ExamSubmission).count(),
    )


@router.get("/feedback", response_model=schemas.AdminFeedbackListOut)
def list_feedback(
    current_user: StatsUser,
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    if status_filter is not None and status_filter not in {"new", "in_progress", "resolved"}:
        raise HTTPException(status_code=422, detail="Unsupported feedback status")
    query = db.query(models.FeedbackEntry).options(joinedload(models.FeedbackEntry.user))
    if status_filter is not None:
        query = query.filter(models.FeedbackEntry.status == status_filter)
    entries, total = apply_pagination(query.order_by(models.FeedbackEntry.created_at.desc()), page, page_size)
    return schemas.AdminFeedbackListOut(
        items=[_admin_feedback_out(entry) for entry in entries],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch("/feedback/{feedback_id}", response_model=schemas.AdminFeedbackOut)
def update_feedback(
    feedback_id: int,
    body: schemas.AdminFeedbackUpdate,
    current_user: StatsUser,
    db: Session = Depends(get_db),
):
    entry = (
        db.query(models.FeedbackEntry)
        .options(joinedload(models.FeedbackEntry.user))
        .filter(models.FeedbackEntry.id == feedback_id)
        .first()
    )
    if entry is None:
        raise HTTPException(status_code=404, detail="Feedback not found")
    entry.status = body.status
    entry.admin_reply = body.admin_reply
    entry.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(entry)
    return _admin_feedback_out(entry)
