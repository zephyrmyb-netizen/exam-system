"""Course business service.

Routers keep the public API contract stable while business rules move here
incrementally.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..repositories.course_repo import CourseRepository


def get_accessible_course(db: Session, course_id: int, user_id: int) -> models.QuestionBank:
    """Return a course if it exists and the user has access (own private or any public)."""
    return CourseService(db).get_accessible_course(course_id, user_id)


def get_owned_course(db: Session, course_id: int, user_id: int) -> models.QuestionBank:
    """Return a course if it exists and the current user owns it."""
    return CourseService(db).get_owned_course(course_id, user_id)


class CourseService:
    def __init__(self, db: Session, repo: CourseRepository | None = None):
        self.db = db
        self.repo = repo or CourseRepository(db)

    def get_accessible_course(self, course_id: int, user_id: int) -> models.QuestionBank:
        bank = self.repo.get_by_id(course_id)
        if not bank:
            raise HTTPException(status_code=404, detail="课程不存在")
        collaboration = (
            self.db.query(models.Collaboration.id)
            .filter(models.Collaboration.course_id == course_id, models.Collaboration.user_id == user_id)
            .first()
        )
        if bank.visibility == "private" and bank.owner_id != user_id and collaboration is None:
            raise HTTPException(status_code=404, detail="课程不存在")
        return bank

    def get_owned_course(self, course_id: int, user_id: int) -> models.QuestionBank:
        bank = self.repo.get_by_id(course_id)
        if not bank:
            raise HTTPException(status_code=404, detail="课程不存在")
        if bank.owner_id != user_id:
            raise HTTPException(status_code=403, detail="只能操作自己的课程")
        return bank

    def create_course(self, data: schemas.CourseCreate, owner_id: int) -> models.QuestionBank:
        if not data.name.strip():
            raise HTTPException(status_code=400, detail="Course name cannot be empty")
        return self.repo.create(owner_id=owner_id, data=data)

    def list_visible(
        self,
        *,
        user_id: int,
        page: int = 0,
        page_size: int = 0,
    ) -> tuple[list[models.QuestionBank], int]:
        return self.repo.get_visible(user_id=user_id, page=page, page_size=page_size)

    def list_owned(
        self,
        *,
        user_id: int,
        page: int = 0,
        page_size: int = 0,
    ) -> tuple[list[models.QuestionBank], int]:
        return self.repo.get_owned(owner_id=user_id, page=page, page_size=page_size)
