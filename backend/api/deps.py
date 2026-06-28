"""Dependency factories for service-layer access."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import User
from ..services.analytics_service import AnalyticsService
from ..services.course_service import CourseService
from ..services.exam_service import ExamService
from ..services.permission_service import PermissionService
from ..services.practice_service import PracticeService
from ..services.recommendation_service import RecommendationService
from ..services.tag_service import TagService

DbSession = Annotated[Session, Depends(get_db)]


def get_course_service(db: DbSession) -> CourseService:
    return CourseService(db)


def get_practice_service(db: DbSession) -> PracticeService:
    return PracticeService(db)


def get_exam_service(db: DbSession) -> ExamService:
    return ExamService(db)


def get_permission_service(db: DbSession) -> PermissionService:
    return PermissionService(db)


def get_tag_service(db: DbSession) -> TagService:
    return TagService(db)


def get_recommendation_service(db: DbSession) -> RecommendationService:
    return RecommendationService(db)


def get_analytics_service(db: DbSession) -> AnalyticsService:
    return AnalyticsService(db)


def require_permission(permission: str):
    def _checker(
        current_user: User = Depends(get_current_user),
        permission_service: PermissionService = Depends(get_permission_service),
    ) -> User:
        permission_service.assert_can(current_user, permission)
        return current_user

    return _checker
