"""Formal exam business service."""

import json

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..repositories.course_repo import CourseRepository
from ..repositories.exam_repo import ExamRepository
from ..utils import normalize_answer


class ExamService:
    def __init__(
        self,
        db: Session,
        exam_repo: ExamRepository | None = None,
        course_repo: CourseRepository | None = None,
    ):
        self.db = db
        self.exam_repo = exam_repo or ExamRepository(db)
        self.course_repo = course_repo or CourseRepository(db)

    def create_exam(self, data: schemas.ExamCreate, *, creator_id: int) -> models.Exam:
        if not data.title.strip():
            raise HTTPException(status_code=400, detail="Exam title cannot be empty")

        course = self.course_repo.get_by_id(data.course_id)
        if course is None:
            raise HTTPException(status_code=404, detail="Course not found")
        if course.owner_id != creator_id:
            raise HTTPException(status_code=403, detail="Only the course owner can create exams")

        if data.question_ids:
            found = (
                self.db.query(models.Question.id)
                .filter(
                    models.Question.course_id == data.course_id,
                    models.Question.id.in_(data.question_ids),
                )
                .all()
            )
            found_ids = {row[0] for row in found}
            missing = [question_id for question_id in data.question_ids if question_id not in found_ids]
            if missing:
                raise HTTPException(status_code=400, detail=f"Questions not in course: {missing}")

        return self.exam_repo.create_exam(data, creator_id=creator_id)

    def publish_exam(self, exam_id: int, user_id: int) -> models.Exam:
        exam = self.exam_repo.get_by_id_with_questions(exam_id)
        if exam is None:
            raise HTTPException(status_code=404, detail="Exam not found")
        if exam.creator_id != user_id:
            raise HTTPException(status_code=403, detail="Only the creator can publish this exam")
        return self.exam_repo.update_status(exam_id, "published")

    def list_published(
        self,
        *,
        page: int = 0,
        page_size: int = 0,
    ) -> tuple[list[models.Exam], int]:
        return self.exam_repo.list_published(page=page, page_size=page_size)

    def list_created(
        self,
        *,
        creator_id: int,
        page: int = 0,
        page_size: int = 0,
    ) -> tuple[list[models.Exam], int]:
        return self.exam_repo.list_created(creator_id=creator_id, page=page, page_size=page_size)

    def get_detail(self, exam_id: int, user_id: int) -> models.Exam:
        exam = self.exam_repo.get_by_id_with_questions(exam_id)
        if exam is None:
            raise HTTPException(status_code=404, detail="Exam not found")
        if exam.status != "published" and exam.creator_id != user_id:
            raise HTTPException(status_code=404, detail="Exam not found")
        return exam

    def start_attempt(self, exam_id: int, user_id: int) -> models.ExamSubmission:
        exam = self.exam_repo.get_by_id_with_questions(exam_id)
        if exam is None or exam.status != "published":
            raise HTTPException(status_code=404, detail="Exam not found")

        existing = self.exam_repo.get_active_submission(exam_id=exam_id, user_id=user_id)
        if existing is not None:
            return existing
        return self.exam_repo.create_submission(exam_id=exam_id, user_id=user_id)

    def submit_exam(
        self,
        exam_id: int,
        user_id: int,
        data: schemas.ExamSubmissionCreate,
    ) -> schemas.ExamResultOut:
        exam = self.exam_repo.get_by_id_with_questions(exam_id)
        if exam is None or exam.status != "published":
            raise HTTPException(status_code=404, detail="Exam not found")

        submission = self.exam_repo.get_active_submission(exam_id=exam_id, user_id=user_id)
        if submission is None:
            submission = self.exam_repo.create_submission(exam_id=exam_id, user_id=user_id)

        correct_count = 0
        total_questions = len(exam.questions)
        per_question_score = self._score_per_question(exam)

        for exam_question in exam.questions:
            question = exam_question.question
            user_answer = data.answers.get(str(question.id), "")
            if self._is_correct(question, user_answer):
                correct_count += 1

        wrong_count = max(total_questions - correct_count, 0)
        score = min(correct_count * per_question_score, exam.total_score)
        accuracy_rate = round((correct_count / total_questions) * 100, 2) if total_questions else 0.0
        submitted = self.exam_repo.submit(
            submission,
            answers_json=json.dumps(data.answers, ensure_ascii=False),
            score=score,
            is_passed=score >= exam.total_score * 0.6,
        )

        return schemas.ExamResultOut(
            exam_id=exam.id,
            submission_id=submitted.id,
            score=score,
            total_score=exam.total_score,
            correct_count=correct_count,
            wrong_count=wrong_count,
            accuracy_rate=accuracy_rate,
            submitted_at=submitted.submitted_at.isoformat() if submitted.submitted_at else None,
        )

    def _score_per_question(self, exam: models.Exam) -> int:
        if not exam.questions:
            return 0
        return max(int(exam.total_score / len(exam.questions)), 1)

    def _is_correct(self, question: models.Question, user_answer: str) -> bool:
        return normalize_answer(user_answer, question.type) == normalize_answer(question.answer, question.type)
