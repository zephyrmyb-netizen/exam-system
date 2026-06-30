"""Exam repository for formal exam mode."""

from datetime import UTC, datetime

from sqlalchemy.orm import selectinload

from .. import models, schemas
from ..crud_common import apply_pagination
from .base import BaseRepository


class ExamRepository(BaseRepository[models.Exam]):
    model = models.Exam

    def create_exam(self, data: schemas.ExamCreate, *, creator_id: int) -> models.Exam:
        exam = models.Exam(
            title=data.title.strip(),
            description=data.description,
            course_id=data.course_id,
            creator_id=creator_id,
            time_limit=data.time_limit,
            total_score=data.total_score,
            is_shuffle=1 if data.is_shuffle else 0,
            is_blind=1 if data.is_blind else 0,
            status="draft",
            created_at=datetime.now(UTC),
        )
        self.db.add(exam)
        self.db.flush()

        for index, question_id in enumerate(data.question_ids):
            self.db.add(
                models.ExamQuestion(
                    exam_id=exam.id,
                    question_id=question_id,
                    score=1,
                    order_index=index,
                )
            )

        self.db.commit()
        return self.get_by_id_with_questions(exam.id)

    def get_by_id_with_questions(self, exam_id: int) -> models.Exam | None:
        return (
            self.query()
            .options(selectinload(models.Exam.questions).selectinload(models.ExamQuestion.question))
            .filter(models.Exam.id == exam_id)
            .first()
        )

    def list_published(self, *, page: int = 0, page_size: int = 0) -> tuple[list[models.Exam], int]:
        query = (
            self.query()
            .options(selectinload(models.Exam.questions))
            .filter(models.Exam.status == "published")
            .order_by(models.Exam.created_at.desc())
        )
        return apply_pagination(query, page, page_size)

    def list_created(
        self,
        *,
        creator_id: int,
        page: int = 0,
        page_size: int = 0,
    ) -> tuple[list[models.Exam], int]:
        query = (
            self.query()
            .options(selectinload(models.Exam.questions))
            .filter(models.Exam.creator_id == creator_id)
            .order_by(models.Exam.created_at.desc())
        )
        return apply_pagination(query, page, page_size)

    def update_status(self, exam_id: int, status: str) -> models.Exam | None:
        exam = self.get_by_id(exam_id)
        if exam is None:
            return None
        exam.status = status
        self.db.commit()
        return self.get_by_id_with_questions(exam_id)

    def get_active_submission(self, *, exam_id: int, user_id: int) -> models.ExamSubmission | None:
        return (
            self.db.query(models.ExamSubmission)
            .filter(
                models.ExamSubmission.exam_id == exam_id,
                models.ExamSubmission.user_id == user_id,
                models.ExamSubmission.submitted_at.is_(None),
            )
            .order_by(models.ExamSubmission.started_at.desc())
            .first()
        )

    def create_submission(self, *, exam_id: int, user_id: int) -> models.ExamSubmission:
        submission = models.ExamSubmission(
            exam_id=exam_id,
            user_id=user_id,
            started_at=datetime.now(UTC),
        )
        self.db.add(submission)
        self.db.commit()
        self.db.refresh(submission)
        return submission

    def submit(
        self,
        submission: models.ExamSubmission,
        *,
        answers_json: str,
        score: int,
        is_passed: bool,
    ) -> models.ExamSubmission:
        submission.answers = answers_json
        submission.score = score
        submission.is_passed = 1 if is_passed else 0
        submission.submitted_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(submission)
        return submission

    def list_submitted(self, exam_id: int) -> list[models.ExamSubmission]:
        return (
            self.db.query(models.ExamSubmission)
            .options(selectinload(models.ExamSubmission.user))
            .filter(
                models.ExamSubmission.exam_id == exam_id,
                models.ExamSubmission.submitted_at.isnot(None),
            )
            .order_by(
                models.ExamSubmission.score.desc(),
                models.ExamSubmission.submitted_at.asc(),
            )
            .all()
        )
