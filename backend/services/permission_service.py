"""Permission constants and helpers for future RBAC work."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Permission:
    COURSE_CREATE: str = "course:create"
    COURSE_EDIT: str = "course:edit"
    COURSE_DELETE: str = "course:delete"
    EXAM_CREATE: str = "exam:create"
    EXAM_PUBLISH: str = "exam:publish"
    USER_MANAGE: str = "user:manage"
