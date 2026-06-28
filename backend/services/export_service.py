"""Data export service for courses and practice history."""

import csv
import io
import json

from sqlalchemy.orm import Session

from .. import models


class ExportService:
    def __init__(self, db: Session):
        self.db = db

    def export_course_json(self, course_id: int) -> str:
        course = self._get_course(course_id)
        questions = self._course_questions(course_id)
        return json.dumps(
            {
                "id": course.id,
                "name": course.name,
                "description": course.description or "",
                "subject": course.subject or "",
                "visibility": course.visibility,
                "questions": [self._question_payload(question) for question in questions],
            },
            ensure_ascii=False,
            indent=2,
        )

    def export_course_excel(self, course_id: int) -> bytes:
        from openpyxl import Workbook

        course = self._get_course(course_id)
        questions = self._course_questions(course.id)
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Questions"
        sheet.append(["ID", "Type", "Subject", "Chapter", "Question", "Options", "Answer", "Analysis", "Difficulty"])
        for question in questions:
            sheet.append(
                [
                    question.id,
                    question.type,
                    question.subject or "",
                    question.chapter or "",
                    question.question,
                    json.dumps(question.get_options_dict(), ensure_ascii=False) if question.get_options_dict() else "",
                    question.answer,
                    question.analysis or "",
                    question.difficulty or "",
                ]
            )
        buffer = io.BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()

    def export_practice_history_csv(self, *, user_id: int) -> str:
        records = (
            self.db.query(models.PracticeRecord)
            .filter(models.PracticeRecord.user_id == user_id)
            .order_by(models.PracticeRecord.answered_at.desc(), models.PracticeRecord.id.desc())
            .all()
        )
        buffer = io.StringIO()
        writer = csv.DictWriter(
            buffer,
            fieldnames=[
                "id",
                "question_id",
                "course_id",
                "question_type",
                "is_correct",
                "user_answer",
                "correct_answer",
                "answered_at",
            ],
        )
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "id": record.id,
                    "question_id": record.question_id or "",
                    "course_id": record.course_id or "",
                    "question_type": record.question_type or "",
                    "is_correct": "true" if record.is_correct else "false",
                    "user_answer": record.user_answer or "",
                    "correct_answer": record.correct_answer or "",
                    "answered_at": record.answered_at.isoformat() if record.answered_at else "",
                }
            )
        return buffer.getvalue()

    def _get_course(self, course_id: int) -> models.QuestionBank:
        course = self.db.query(models.QuestionBank).filter(models.QuestionBank.id == course_id).first()
        if course is None:
            raise ValueError("Course not found")
        return course

    def _course_questions(self, course_id: int) -> list[models.Question]:
        return (
            self.db.query(models.Question)
            .filter(models.Question.course_id == course_id)
            .order_by(models.Question.id.asc())
            .all()
        )

    def _question_payload(self, question: models.Question) -> dict:
        return {
            "id": question.id,
            "owner_id": question.owner_id,
            "course_id": question.course_id,
            "visibility": question.visibility,
            "source": question.source,
            "created_at": question.created_at.isoformat() if question.created_at else None,
            "subject": question.subject,
            "chapter": question.chapter,
            "type": question.type,
            "question": question.question,
            "options": question.get_options_dict(),
            "answer": question.answer,
            "analysis": question.analysis or "",
            "difficulty": question.difficulty or "",
        }
