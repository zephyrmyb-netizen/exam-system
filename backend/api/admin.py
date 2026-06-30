"""Minimal admin API for Phase 3 role and platform statistics management."""

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
    if role_name not in {"student", "teacher", "admin"}:
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
