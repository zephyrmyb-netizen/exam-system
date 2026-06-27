"""Dependency factories for service-layer access."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.course_service import CourseService
from ..services.practice_service import PracticeService

DbSession = Annotated[Session, Depends(get_db)]


def get_course_service(db: DbSession) -> CourseService:
    return CourseService(db)


def get_practice_service(db: DbSession) -> PracticeService:
    return PracticeService(db)
