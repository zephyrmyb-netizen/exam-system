"""Dependency factories for service-layer access."""

from fastapi import Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.course_service import CourseService
from ..services.practice_service import PracticeService


def get_course_service(db: Session = Depends(get_db)) -> CourseService:
    return CourseService(db)


def get_practice_service(db: Session = Depends(get_db)) -> PracticeService:
    return PracticeService(db)
