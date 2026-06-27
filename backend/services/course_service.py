"""Course business service.

Routers keep the public API contract stable while business rules move here
incrementally.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..repositories.course_repo import CourseRepository


class CourseService:
    def __init__(self, db: Session, repo: CourseRepository | None = None):
        self.db = db
        self.repo = repo or CourseRepository(db)

    def get_accessible_course(self, course_id: int, user_id: int) -> models.QuestionBank:
        bank = self.repo.get_by_id(course_id)
        if not bank:
            raise HTTPException(status_code=404, detail="课程不存在")
        if bank.visibility == "private" and bank.owner_id != user_id:
            raise HTTPException(status_code=404, detail="课程不存在")
        return bank

    def get_owned_course(self, course_id: int, user_id: int) -> models.QuestionBank:
        bank = self.repo.get_by_id(course_id)
        if not bank:
            raise HTTPException(status_code=404, detail="课程不存在")
        if bank.owner_id != user_id:
            raise HTTPException(status_code=403, detail="只能操作自己的课程")
        return bank

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
