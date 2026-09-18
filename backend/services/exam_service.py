"""Formal exam business service."""

import json
import secrets
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import crud_wrongbook, models, schemas
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
            raise HTTPException(status_code=400, detail="考试标题不能为空")

        course = self.course_repo.get_by_id(data.course_id)
        if course is None:
            raise HTTPException(status_code=404, detail="课程不存在")
        if course.owner_id != creator_id:
            raise HTTPException(status_code=403, detail="只有课程所有者可以创建考试")

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
                raise HTTPException(status_code=400, detail=f"以下题目不在该课程中：{missing}")

        self._validate_schedule(data.start_at, data.end_at)
        # Draft codes cannot resolve; the code becomes usable only after publish.
        return self.exam_repo.create_exam(data, creator_id=creator_id, share_code=self._new_share_code())

    def publish_exam(self, exam_id: int, user_id: int) -> models.Exam:
        exam = self.exam_repo.get_by_id_with_questions(exam_id)
        if exam is None:
            raise HTTPException(status_code=404, detail="考试不存在")
        if exam.creator_id != user_id:
            raise HTTPException(status_code=403, detail="只有创建者可以发布此考试")
        self._validate_schedule(exam.start_at, exam.end_at)
        if not exam.share_code:
            exam.share_code = self._new_share_code()
            self.db.commit()
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
            raise HTTPException(status_code=404, detail="考试不存在")
        if exam.status != "published" and exam.creator_id != user_id:
            raise HTTPException(status_code=404, detail="考试不存在")
        return exam

    def start_attempt(self, exam_id: int, user_id: int) -> models.ExamSubmission:
        exam = self.exam_repo.get_by_id_with_questions(exam_id)
        if exam is None or exam.status != "published":
            raise HTTPException(status_code=404, detail="考试不存在")

        availability = self.availability(exam)
        if availability == "scheduled":
            raise HTTPException(status_code=403, detail="Exam has not opened yet")
        if availability == "closed":
            raise HTTPException(status_code=403, detail="Exam is closed")

        existing = self.exam_repo.get_active_submission(exam_id=exam_id, user_id=user_id)
        if existing is not None:
            return existing
        return self.exam_repo.create_submission(exam_id=exam_id, user_id=user_id)

    def get_shared_detail(self, share_code: str) -> models.Exam:
        exam = (
            self.db.query(models.Exam)
            .filter(models.Exam.share_code == share_code.upper(), models.Exam.status == "published")
            .first()
        )
        if exam is None:
            raise HTTPException(status_code=404, detail="Shared exam not found")
        return self.exam_repo.get_by_id_with_questions(exam.id) or exam

    def availability(self, exam: models.Exam, now: datetime | None = None) -> str:
        if exam.status != "published":
            return "draft"
        current = now or datetime.now(UTC)
        start_at = self._as_utc(exam.start_at)
        end_at = self._as_utc(exam.end_at)
        if start_at and current < start_at:
            return "scheduled"
        if end_at and current >= end_at:
            return "closed"
        return "active"

    def _new_share_code(self) -> str:
        for _ in range(20):
            code = secrets.token_hex(4).upper()
            if not self.db.query(models.Exam.id).filter(models.Exam.share_code == code).first():
                return code
        raise HTTPException(status_code=503, detail="Could not allocate a share code")

    @staticmethod
    def _as_utc(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)

    def _validate_schedule(self, start_at: datetime | None, end_at: datetime | None) -> None:
        start = self._as_utc(start_at)
        end = self._as_utc(end_at)
        if start and end and end <= start:
            raise HTTPException(status_code=400, detail="End time must be later than start time")

    def submit_exam(
        self,
        exam_id: int,
        user_id: int,
        data: schemas.ExamSubmissionCreate,
    ) -> schemas.ExamResultOut:
        exam = self.exam_repo.get_by_id_with_questions(exam_id)
        if exam is None or exam.status != "published":
            raise HTTPException(status_code=404, detail="考试不存在")

        submission = self.exam_repo.get_active_submission(exam_id=exam_id, user_id=user_id)
        if submission is None:
            # Idempotency check: if the user already submitted this exam, return
            # the existing result instead of creating and submitting a new record.
            already_submitted = (
                self.db.query(models.ExamSubmission)
                .filter(
                    models.ExamSubmission.exam_id == exam_id,
                    models.ExamSubmission.user_id == user_id,
                    models.ExamSubmission.submitted_at.isnot(None),
                )
                .order_by(models.ExamSubmission.submitted_at.desc())
                .first()
            )
            if already_submitted is not None:
                return self._result_from_submission(exam, already_submitted)
            submission = self.exam_repo.create_submission(exam_id=exam_id, user_id=user_id)

        correct_count = 0
        question_results: dict[str, dict[str, object]] = {}
        total_questions = len(exam.questions)
        per_question_score = self._score_per_question(exam)

        for exam_question in exam.questions:
            question = exam_question.question
            user_answer = data.answers.get(str(question.id), "")
            is_correct = self._is_correct(question, user_answer)
            question_results[str(question.id)] = {"correct": is_correct, "answer": user_answer}
            if is_correct:
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
            question_results=question_results,
        )

    def _result_from_submission(
        self,
        exam: models.Exam,
        submission: models.ExamSubmission,
    ) -> schemas.ExamResultOut:
        """Rebuild an :class:`ExamResultOut` from an already-submitted record.

        Used for idempotent returns so a repeated ``submit_exam`` call yields
        the same result as the original submission without creating a new row.
        """
        try:
            answers = json.loads(submission.answers) if submission.answers else {}
        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=500,
                detail="已保存的答卷数据损坏，请联系管理员重置",
            ) from exc

        correct_count = 0
        question_results: dict[str, dict[str, object]] = {}
        total_questions = len(exam.questions)
        for exam_question in exam.questions:
            question = exam_question.question
            user_answer = answers.get(str(question.id), "")
            is_correct = self._is_correct(question, user_answer)
            question_results[str(question.id)] = {"correct": is_correct, "answer": user_answer}
            if is_correct:
                correct_count += 1

        wrong_count = max(total_questions - correct_count, 0)
        accuracy_rate = round((correct_count / total_questions) * 100, 2) if total_questions else 0.0
        return schemas.ExamResultOut(
            exam_id=exam.id,
            submission_id=submission.id,
            score=submission.score or 0,
            total_score=exam.total_score,
            correct_count=correct_count,
            wrong_count=wrong_count,
            accuracy_rate=accuracy_rate,
            submitted_at=submission.submitted_at.isoformat() if submission.submitted_at else None,
            question_results=question_results,
        )

    def add_submission_wrong_answers_to_wrongbook(self, exam_id: int, user_id: int) -> int:
        exam = self.exam_repo.get_by_id_with_questions(exam_id)
        if exam is None or exam.status != "published":
            raise HTTPException(status_code=404, detail="Exam not found")
        submission = (
            self.db.query(models.ExamSubmission)
            .filter(
                models.ExamSubmission.exam_id == exam_id,
                models.ExamSubmission.user_id == user_id,
                models.ExamSubmission.submitted_at.isnot(None),
            )
            .order_by(models.ExamSubmission.submitted_at.desc())
            .first()
        )
        if submission is None:
            raise HTTPException(status_code=400, detail="Submit the exam before adding wrong answers")
        try:
            answers = json.loads(submission.answers) if submission.answers else {}
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=500, detail="Saved answer data is invalid") from exc

        added_count = 0
        for exam_question in exam.questions:
            question = exam_question.question
            user_answer = answers.get(str(question.id), "")
            if not self._is_correct(question, user_answer):
                crud_wrongbook.upsert_wrong_record(self.db, user_id, question.id, user_answer)
                added_count += 1
        self.db.commit()
        return added_count

    def get_leaderboard(self, exam_id: int, user_id: int) -> schemas.ExamLeaderboardOut:
        exam = self.exam_repo.get_by_id_with_questions(exam_id)
        if exam is None or (exam.status != "published" and exam.creator_id != user_id):
            raise HTTPException(status_code=404, detail="考试不存在")

        entries = []
        for index, submission in enumerate(self.exam_repo.list_submitted(exam_id), start=1):
            entries.append(
                schemas.ExamLeaderboardEntry(
                    rank=index,
                    user_id=submission.user_id,
                    username=submission.user.username if submission.user else f"user-{submission.user_id}",
                    score=submission.score or 0,
                    total_score=exam.total_score,
                    submitted_at=submission.submitted_at.isoformat() if submission.submitted_at else None,
                )
            )
        return schemas.ExamLeaderboardOut(exam_id=exam_id, entries=entries, total=len(entries))

    def _score_per_question(self, exam: models.Exam) -> int:
        if not exam.questions:
            return 0
        return max(int(exam.total_score / len(exam.questions)), 1)

    def _is_correct(self, question: models.Question, user_answer: str) -> bool:
        return normalize_answer(user_answer, question.type) == normalize_answer(question.answer, question.type)
