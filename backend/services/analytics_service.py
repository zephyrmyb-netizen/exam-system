"""Data analytics aggregation for Phase 4."""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models
from ..config import APP_TIMEZONE


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        self.local_tz = ZoneInfo(APP_TIMEZONE)

    def get_daily_activity(self, *, user_id: int, days: int = 30) -> list[dict]:
        safe_days = max(1, min(days, 365))
        today = datetime.now(self.local_tz).date()
        start = today - timedelta(days=safe_days - 1)
        counts = {start + timedelta(days=offset): 0 for offset in range(safe_days)}

        records = (
            self.db.query(models.PracticeRecord.answered_at)
            .filter(models.PracticeRecord.user_id == user_id)
            .filter(models.PracticeRecord.answered_at >= self._start_of_day_utc(start))
            .all()
        )
        for (answered_at,) in records:
            local_day = self._to_local_date(answered_at)
            if local_day in counts:
                counts[local_day] += 1

        return [{"date": day.isoformat(), "count": count} for day, count in counts.items()]

    def get_type_distribution(self, *, user_id: int) -> list[dict]:
        rows = (
            self.db.query(
                models.PracticeRecord.question_type.label("question_type"),
                func.count(models.PracticeRecord.id).label("total_count"),
                func.coalesce(func.sum(models.PracticeRecord.is_correct), 0).label("correct_count"),
            )
            .filter(models.PracticeRecord.user_id == user_id)
            .group_by(models.PracticeRecord.question_type)
            .order_by(models.PracticeRecord.question_type.asc())
            .all()
        )

        result = []
        for row in rows:
            total = int(row.total_count or 0)
            correct = int(row.correct_count or 0)
            result.append(
                {
                    "question_type": row.question_type or "unknown",
                    "total_count": total,
                    "correct_count": correct,
                    "wrong_count": max(total - correct, 0),
                    "accuracy_rate": round(correct / total, 4) if total else 0.0,
                }
            )
        return result

    def get_streak(self, *, user_id: int) -> dict:
        rows = (
            self.db.query(models.PracticeRecord.answered_at)
            .filter(models.PracticeRecord.user_id == user_id)
            .order_by(models.PracticeRecord.answered_at.desc())
            .all()
        )
        active_days = {self._to_local_date(answered_at) for (answered_at,) in rows}
        if not active_days:
            return {"current_streak": 0, "longest_streak": 0, "last_practiced_date": None}

        today = datetime.now(self.local_tz).date()
        cursor = today if today in active_days else today - timedelta(days=1)
        current = 0
        while cursor in active_days:
            current += 1
            cursor -= timedelta(days=1)

        longest = self._longest_streak(active_days)
        return {
            "current_streak": current,
            "longest_streak": longest,
            "last_practiced_date": max(active_days).isoformat(),
        }

    def get_course_stats_for_owner(self, *, owner_id: int) -> list[dict]:
        courses = (
            self.db.query(models.QuestionBank)
            .filter(models.QuestionBank.owner_id == owner_id)
            .order_by(models.QuestionBank.created_at.desc(), models.QuestionBank.id.desc())
            .all()
        )
        if not courses:
            return []

        course_ids = [course.id for course in courses]
        question_counts = dict(
            self.db.query(models.Question.course_id, func.count(models.Question.id))
            .filter(models.Question.course_id.in_(course_ids))
            .group_by(models.Question.course_id)
            .all()
        )
        practice_rows = (
            self.db.query(
                models.PracticeRecord.course_id,
                func.count(models.PracticeRecord.id).label("total_count"),
                func.coalesce(func.sum(models.PracticeRecord.is_correct), 0).label("correct_count"),
            )
            .filter(models.PracticeRecord.course_id.in_(course_ids))
            .group_by(models.PracticeRecord.course_id)
            .all()
        )
        practice_by_course = {row.course_id: row for row in practice_rows}

        result = []
        for course in courses:
            stats = practice_by_course.get(course.id)
            total = int(stats.total_count or 0) if stats else 0
            correct = int(stats.correct_count or 0) if stats else 0
            result.append(
                {
                    "course_id": course.id,
                    "course_name": course.name,
                    "question_count": int(question_counts.get(course.id, 0)),
                    "practice_count": total,
                    "accuracy_rate": round(correct / total, 4) if total else 0.0,
                }
            )
        return result

    def get_score_distribution(self, *, exam_id: int) -> list[dict]:
        buckets = [
            {"label": "0-59", "min": 0, "max": 59, "count": 0},
            {"label": "60-69", "min": 60, "max": 69, "count": 0},
            {"label": "70-79", "min": 70, "max": 79, "count": 0},
            {"label": "80-89", "min": 80, "max": 89, "count": 0},
            {"label": "90-100", "min": 90, "max": 100, "count": 0},
        ]
        scores = (
            self.db.query(models.ExamSubmission.score)
            .filter(
                models.ExamSubmission.exam_id == exam_id,
                models.ExamSubmission.score.is_not(None),
            )
            .all()
        )
        for (score,) in scores:
            safe_score = int(score or 0)
            for bucket in buckets:
                if bucket["min"] <= safe_score <= bucket["max"]:
                    bucket["count"] += 1
                    break
        return [{"label": bucket["label"], "count": bucket["count"]} for bucket in buckets]

    def _to_local_date(self, value: datetime) -> date:
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(self.local_tz).date()

    def _start_of_day_utc(self, local_day: date) -> datetime:
        return datetime.combine(local_day, time.min, tzinfo=self.local_tz).astimezone(UTC)

    def _longest_streak(self, active_days: set[date]) -> int:
        longest = 0
        remaining = set(active_days)
        while remaining:
            day = remaining.pop()
            streak = 1
            cursor = day - timedelta(days=1)
            while cursor in remaining:
                remaining.remove(cursor)
                streak += 1
                cursor -= timedelta(days=1)
            cursor = day + timedelta(days=1)
            while cursor in remaining:
                remaining.remove(cursor)
                streak += 1
                cursor += timedelta(days=1)
            longest = max(longest, streak)
        return longest
