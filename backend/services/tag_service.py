"""Knowledge tag business logic."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models
from ..repositories.tag_repo import QuestionTagRepository, TagRepository


class TagService:
    def __init__(
        self,
        db: Session,
        repo: TagRepository | None = None,
        question_tags: QuestionTagRepository | None = None,
    ):
        self.db = db
        self.repo = repo or TagRepository(db)
        self.question_tags = question_tags or QuestionTagRepository(db)

    def list_tags(
        self,
        *,
        keyword: str = "",
        page: int = 0,
        page_size: int = 0,
    ) -> tuple[list[models.Tag], int]:
        return self.repo.search(keyword=keyword, page=page, page_size=page_size)

    def create_tag(
        self,
        *,
        name: str,
        color: str = "",
        parent_id: int | None = None,
    ) -> models.Tag:
        if not name.strip():
            raise ValueError("Tag name cannot be empty")
        return self.repo.get_or_create(name=name, color=color, parent_id=parent_id)

    def tag_question(self, *, question_id: int, tag_names: list[str]) -> list[models.Tag]:
        seen: set[str] = set()
        tags: list[models.Tag] = []
        for raw_name in tag_names:
            name = raw_name.strip()
            normalized = name.lower()
            if not name or normalized in seen:
                continue
            seen.add(normalized)
            tag = self.repo.get_or_create(name=name)
            self.question_tags.add(question_id=question_id, tag_id=tag.id)
            tags.append(tag)
        return self.question_tags.list_for_question(question_id)

    def list_question_tags(self, question_id: int) -> list[models.Tag]:
        return self.question_tags.list_for_question(question_id)

    def replace_question_tags(self, *, question_id: int, tag_names: list[str]) -> list[models.Tag]:
        self.question_tags.clear_for_question(question_id)
        return self.tag_question(question_id=question_id, tag_names=tag_names)

    def get_accuracy_by_tag(self, *, user_id: int) -> list[dict]:
        rows = (
            self.db.query(
                models.Tag.id.label("tag_id"),
                models.Tag.name.label("tag_name"),
                func.count(models.PracticeRecord.id).label("total_count"),
                func.coalesce(func.sum(models.PracticeRecord.is_correct), 0).label("correct_count"),
            )
            .join(models.QuestionTag, models.QuestionTag.tag_id == models.Tag.id)
            .join(models.PracticeRecord, models.PracticeRecord.question_id == models.QuestionTag.question_id)
            .filter(models.PracticeRecord.user_id == user_id)
            .group_by(models.Tag.id, models.Tag.name)
            .order_by(models.Tag.name.asc(), models.Tag.id.asc())
            .all()
        )

        result = []
        for row in rows:
            total = int(row.total_count or 0)
            correct = int(row.correct_count or 0)
            result.append(
                {
                    "tag_id": row.tag_id,
                    "tag_name": row.tag_name,
                    "total_count": total,
                    "correct_count": correct,
                    "accuracy_rate": correct / total if total else 0.0,
                }
            )
        return result
