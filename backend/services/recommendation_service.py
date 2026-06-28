"""Smart recommendation engine for Phase 4."""

from sqlalchemy import case, desc, func
from sqlalchemy.orm import Session

from .. import models
from ..crud_practice import get_due_reviews, get_weak_types
from .tag_service import TagService

WEAK_ACCURACY_THRESHOLD = 0.7
DEFAULT_WEAK_QUESTION_LIMIT = 20


class RecommendationService:
    def __init__(self, db: Session, tag_service: TagService | None = None):
        self.db = db
        self.tag_service = tag_service or TagService(db)

    def get_today_recommendation(self, *, user_id: int) -> dict:
        weak_tags = [
            item
            for item in self.tag_service.get_accuracy_by_tag(user_id=user_id)
            if item["total_count"] > 0 and item["accuracy_rate"] < WEAK_ACCURACY_THRESHOLD
        ]
        due_reviews = get_due_reviews(self.db, user_id=user_id, limit=100)
        weak_types = get_weak_types(self.db, user_id=user_id)
        due_question_ids = [review.question_id for review in due_reviews if review.question_id is not None]

        return {
            "weak_tags": weak_tags,
            "weak_types": weak_types,
            "due_count": len(due_reviews),
            "due_question_ids": due_question_ids,
            "recommended_modes": self._recommended_modes(
                weak_tags=weak_tags,
                weak_types=weak_types,
                due_count=len(due_reviews),
            ),
        }

    def get_weak_questions(
        self,
        *,
        user_id: int,
        limit: int = DEFAULT_WEAK_QUESTION_LIMIT,
    ) -> list[models.Question]:
        rows = (
            self.db.query(
                models.PracticeRecord.question_id,
                func.count(models.PracticeRecord.id).label("total_count"),
                func.sum(case((models.PracticeRecord.is_correct == 0, 1), else_=0)).label("wrong_count"),
            )
            .filter(
                models.PracticeRecord.user_id == user_id,
                models.PracticeRecord.question_id.is_not(None),
            )
            .group_by(models.PracticeRecord.question_id)
            .having(func.sum(case((models.PracticeRecord.is_correct == 0, 1), else_=0)) > 0)
            .order_by(desc("wrong_count"), desc("total_count"))
            .limit(limit)
            .all()
        )
        question_ids = [row.question_id for row in rows]
        if not question_ids:
            return []

        question_by_id = {
            question.id: question
            for question in self.db.query(models.Question).filter(models.Question.id.in_(question_ids)).all()
        }
        return [question_by_id[question_id] for question_id in question_ids if question_id in question_by_id]

    def _recommended_modes(self, *, weak_tags: list[dict], weak_types: list[dict], due_count: int) -> list[str]:
        modes = []
        if weak_tags:
            modes.append("weak_tag_practice")
        if weak_types:
            modes.append("weak_type_practice")
        if due_count > 0:
            modes.append("spaced_repeat")
        if not modes:
            modes.append("random_practice")
        return modes
