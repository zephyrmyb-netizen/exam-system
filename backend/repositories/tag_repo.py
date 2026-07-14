"""Knowledge tag repositories."""

from sqlalchemy import func

from .. import models
from ..crud_common import apply_pagination
from .base import BaseRepository


class TagRepository(BaseRepository[models.Tag]):
    model = models.Tag

    def get_by_name(self, name: str) -> models.Tag | None:
        normalized = name.strip().lower()
        if not normalized:
            return None
        return self.query().filter(func.lower(models.Tag.name) == normalized).first()

    def get_or_create(
        self,
        *,
        name: str,
        color: str = "",
        parent_id: int | None = None,
    ) -> models.Tag:
        normalized = name.strip()
        existing = self.get_by_name(normalized)
        if existing:
            return existing

        tag = models.Tag(name=normalized, color=color or "", parent_id=parent_id)
        self.db.add(tag)
        self.db.commit()
        self.db.refresh(tag)
        return tag

    def search(
        self,
        *,
        keyword: str = "",
        page: int = 0,
        page_size: int = 0,
    ) -> tuple[list[models.Tag], int]:
        query = self.query()
        if keyword.strip():
            query = query.filter(models.Tag.name.like(f"%{keyword.strip()}%"))
        query = query.order_by(models.Tag.name.asc(), models.Tag.id.asc())
        return apply_pagination(query, page, page_size)


class QuestionTagRepository(BaseRepository[models.QuestionTag]):
    model = models.QuestionTag

    def add(self, *, question_id: int, tag_id: int) -> models.QuestionTag:
        existing = (
            self.query()
            .filter(
                models.QuestionTag.question_id == question_id,
                models.QuestionTag.tag_id == tag_id,
            )
            .first()
        )
        if existing:
            return existing

        relation = models.QuestionTag(question_id=question_id, tag_id=tag_id)
        self.db.add(relation)
        self.db.commit()
        self.db.refresh(relation)
        return relation

    def list_for_question(self, question_id: int) -> list[models.Tag]:
        rows = (
            self.db.query(models.Tag)
            .join(models.QuestionTag, models.QuestionTag.tag_id == models.Tag.id)
            .filter(models.QuestionTag.question_id == question_id)
            .order_by(models.QuestionTag.id.asc())
            .all()
        )
        return rows

    def clear_for_question(self, question_id: int) -> int:
        deleted = self.query().filter(models.QuestionTag.question_id == question_id).delete()
        self.db.commit()
        return deleted
