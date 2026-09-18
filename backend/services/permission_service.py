"""Permission constants and role-based permission checks."""

from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models


@dataclass(frozen=True)
class Permission:
    COURSE_CREATE: str = "course:create"
    COURSE_EDIT: str = "course:edit"
    COURSE_DELETE: str = "course:delete"
    EXAM_CREATE: str = "exam:create"
    EXAM_PUBLISH: str = "exam:publish"
    USER_MANAGE: str = "user:manage"


_STUDENT_PERMISSIONS = {
    "practice:random",
    "practice:submit",
    "practice:review",
    "wrongbook:read",
    "wrongbook:write",
    "course:read",
    "course:create",
    "chat:use",
    "import:use",
    "bookmark:manage",
    "exam:create",
    "exam:publish",
    "exam:view_leaderboard",
}

_ADMIN_PERMISSIONS = _STUDENT_PERMISSIONS | {
    "user:manage",
    "announcement:manage",
    "stats:view_global",
}

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "student": _STUDENT_PERMISSIONS,
    "admin": _ADMIN_PERMISSIONS,
}


class PermissionService:
    """Small RBAC service used by dependency guards and future admin flows."""

    def __init__(self, db: Session):
        self.db = db

    def get_role_name(self, user: models.User) -> str:
        return user.role

    def get_permissions(self, user: models.User) -> set[str]:
        return ROLE_PERMISSIONS.get(self.get_role_name(user), ROLE_PERMISSIONS["student"])

    def can(self, user: models.User, permission: str) -> bool:
        return permission in self.get_permissions(user)

    def assert_can(self, user: models.User, permission: str) -> None:
        if self.can(user, permission):
            return
        raise HTTPException(status_code=403, detail=f"Permission denied: {permission}")
