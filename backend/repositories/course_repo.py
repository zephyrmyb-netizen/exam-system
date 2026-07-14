"""Question-bank/course repository."""

from datetime import UTC, datetime

from sqlalchemy.orm import selectinload

from .. import models, schemas
from ..crud_common import _add_bank_visibility_filter, apply_pagination
from .base import BaseRepository


class CourseRepository(BaseRepository[models.QuestionBank]):
    model = models.QuestionBank

    def create(self, *, owner_id: int, data: schemas.CourseCreate) -> models.QuestionBank:
        bank = models.QuestionBank(
            owner_id=owner_id,
            name=data.name,
            description=data.description,
            subject=data.subject,
            visibility=data.visibility,
            created_at=datetime.now(UTC),
        )
        self.db.add(bank)
        self.db.commit()
        self.db.refresh(bank)
        return bank

    def get_visible(
        self,
        *,
        user_id: int | None,
        page: int = 0,
        page_size: int = 0,
    ) -> tuple[list[models.QuestionBank], int]:
        query = _add_bank_visibility_filter(self.query(), user_id)
        query = query.order_by(models.QuestionBank.created_at.desc())
        return apply_pagination(query, page, page_size)

    def get_owned(
        self,
        *,
        owner_id: int,
        page: int = 0,
        page_size: int = 0,
    ) -> tuple[list[models.QuestionBank], int]:
        query = (
            self.query()
            .filter(models.QuestionBank.owner_id == owner_id)
            .options(selectinload(models.QuestionBank.questions))
            .order_by(models.QuestionBank.created_at.desc())
        )
        return apply_pagination(query, page, page_size)
