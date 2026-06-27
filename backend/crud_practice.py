from datetime import datetime, timedelta, timezone
from random import randint
from typing import Optional

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from . import models
from .config import APP_TIMEZONE
from .crud_common import _add_question_visibility_filter, apply_pagination
from .utils import check_fill_blank_answer, check_short_answer_answer, normalize_answer

_REVIEW_INTERVALS = [1, 3, 7, 14, 30]


def create_practice_record(
    db: Session,
    user_id: int,
    question_id: int,
    course_id: int | None,
    question_type: str | None,
    is_correct: bool,
    user_answer: str,
    correct_answer: str,
) -> models.PracticeRecord:
    record = models.PracticeRecord(
        user_id=user_id,
        question_id=question_id,
        course_id=course_id,
        question_type=question_type,
        is_correct=1 if is_correct else 0,
        user_answer=user_answer,
        correct_answer=correct_answer,
        answered_at=datetime.now(timezone.utc),
    )
    db.add(record)
    db.flush()
    return record


def get_practice_stats(db: Session, user_id: int) -> dict:
    from zoneinfo import ZoneInfo

    now_utc = datetime.now(timezone.utc)
    local_tz = ZoneInfo(APP_TIMEZONE)
    local_midnight = datetime.now(local_tz).replace(hour=0, minute=0, second=0, microsecond=0)
    today_start = local_midnight.astimezone(timezone.utc)
    seven_days_ago = now_utc - timedelta(days=7)

    # Merge multiple COUNT queries into a single aggregation for efficiency.
    row = (
        db.query(
            func.count(models.PracticeRecord.id).label("total"),
            func.sum(
                case((models.PracticeRecord.is_correct == 1, 1), else_=0)
            ).label("correct"),
            func.sum(
                case((models.PracticeRecord.answered_at >= today_start, 1), else_=0)
            ).label("today"),
            func.sum(
                case((models.PracticeRecord.answered_at >= seven_days_ago, 1), else_=0)
            ).label("recent_7d"),
        )
        .filter(models.PracticeRecord.user_id == user_id)
        .first()
    )

    total_count = int(row.total or 0)
    if total_count == 0:
        return {
            "today_count": 0,
            "total_count": 0,
            "correct_count": 0,
            "wrong_count": 0,
            "accuracy_rate": 0.0,
            "recent_count_7d": 0,
        }

    correct_count = int(row.correct or 0)
    today_count = int(row.today or 0)
    recent_count_7d = int(row.recent_7d or 0)
    wrong_count = total_count - correct_count
    accuracy_rate = round(correct_count / total_count, 4)

    return {
        "today_count": today_count,
        "total_count": total_count,
        "correct_count": correct_count,
        "wrong_count": wrong_count,
        "accuracy_rate": accuracy_rate,
        "recent_count_7d": recent_count_7d,
    }


def get_practice_history(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[models.PracticeRecord], int]:
    from sqlalchemy.orm import joinedload

    query = (
        db.query(models.PracticeRecord)
        .filter(models.PracticeRecord.user_id == user_id)
        .options(joinedload(models.PracticeRecord.question))
    )
    query = query.order_by(models.PracticeRecord.answered_at.desc())
    return apply_pagination(query, page, page_size)


def get_practice_stats_by_course(
    db: Session, user_id: int, course_ids: list[int],
) -> dict[int, dict]:
    if not course_ids:
        return {}

    rows = (
        db.query(
            models.PracticeRecord.course_id,
            func.count(models.PracticeRecord.id),
            func.max(models.PracticeRecord.answered_at),
        )
        .filter(
            models.PracticeRecord.user_id == user_id,
            models.PracticeRecord.course_id.in_(course_ids),
        )
        .group_by(models.PracticeRecord.course_id)
        .all()
    )

    result = {}
    for course_id, cnt, last_answered in rows:
        result[course_id] = {
            "practice_count": cnt,
            "last_practiced_at": last_answered.isoformat() if last_answered else None,
        }
    return result


def get_today_review_summary(db: Session, user_id: int) -> dict:
    now = datetime.now(timezone.utc)

    due_count = (
        db.query(models.UserQuestionReview)
        .filter(models.UserQuestionReview.user_id == user_id)
        .filter(
            (models.UserQuestionReview.next_review_at <= now)
            | (models.UserQuestionReview.next_review_at.is_(None))
        )
        .count()
    )

    wrong_base = db.query(models.WrongRecord).filter(models.WrongRecord.user_id == user_id)
    wrong_count = wrong_base.count()

    recent = (
        db.query(models.PracticeRecord)
        .filter(models.PracticeRecord.user_id == user_id)
        .order_by(models.PracticeRecord.answered_at.desc())
        .limit(50)
        .all()
    )

    type_stats = {}
    for r in recent:
        qt = r.question_type or "unknown"
        if qt not in type_stats:
            type_stats[qt] = {"total": 0, "wrong": 0}
        type_stats[qt]["total"] += 1
        if not r.is_correct:
            type_stats[qt]["wrong"] += 1

    weak_types = []
    for qt, stats in type_stats.items():
        if stats["total"] > 0:
            error_rate = round(stats["wrong"] / stats["total"], 4)
            if error_rate >= 0.4:
                weak_types.append({
                    "question_type": qt,
                    "total_attempts": stats["total"],
                    "wrong_attempts": stats["wrong"],
                    "error_rate": error_rate,
                })

    weak_types.sort(key=lambda x: x["error_rate"], reverse=True)

    modes = []
    if wrong_count > 0:
        modes.append("wrong_review")
    if due_count > 0:
        modes.append("spaced_repeat")
    if weak_types:
        modes.append("type_practice")
    if due_count == 0 and wrong_count == 0 and not weak_types:
        modes.append("random_practice")

    return {
        "due_count": due_count,
        "wrong_count": wrong_count,
        "weak_types": weak_types,
        "recommended_modes": modes,
    }


def get_weak_types(
    db: Session, user_id: int, recent_n: int = 50,
) -> list[dict]:
    recent = (
        db.query(models.PracticeRecord)
        .filter(models.PracticeRecord.user_id == user_id)
        .order_by(models.PracticeRecord.answered_at.desc())
        .limit(recent_n)
        .all()
    )

    if not recent:
        return []

    type_stats = {}
    for r in recent:
        qt = r.question_type or "unknown"
        if qt not in type_stats:
            type_stats[qt] = {"total": 0, "wrong": 0}
        type_stats[qt]["total"] += 1
        if not r.is_correct:
            type_stats[qt]["wrong"] += 1

    total_attempts = sum(s["total"] for s in type_stats.values())
    total_wrong = sum(s["wrong"] for s in type_stats.values())
    overall_rate = total_wrong / total_attempts if total_attempts > 0 else 0

    weak_types = []
    for qt, stats in type_stats.items():
        if stats["total"] >= 2:
            rate = round(stats["wrong"] / stats["total"], 4)
            if rate > overall_rate or rate >= 0.4:
                weak_types.append({
                    "question_type": qt,
                    "total_attempts": stats["total"],
                    "wrong_attempts": stats["wrong"],
                    "error_rate": rate,
                })

    weak_types.sort(key=lambda x: x["error_rate"], reverse=True)
    return weak_types


def get_random_question(
    db: Session, user_id: int | None = None, q_type: str = "", chapter: str = "",
) -> Optional[models.Question]:
    """Return a random question visible to *user_id*, using count+offset.

    Avoids ``ORDER BY RANDOM()`` which forces a full-table sort. Instead
    queries the count, picks a random offset, and fetches one row.
    """
    query = _add_question_visibility_filter(db.query(models.Question), user_id)
    if q_type:
        query = query.filter(models.Question.type == q_type)
    if chapter:
        query = query.filter(models.Question.chapter == chapter)
    count = query.count()
    if count == 0:
        return None
    return query.offset(randint(0, count - 1)).limit(1).first()


def get_random_question_in_course(
    db: Session, course_id: int, user_id: int | None = None, q_type: str = "", chapter: str = "",
) -> Optional[models.Question]:
    """Random question in a course, using count+offset instead of ORDER BY RANDOM()."""
    query = _add_question_visibility_filter(
        db.query(models.Question).filter(models.Question.course_id == course_id),
        user_id,
    )
    if q_type:
        query = query.filter(models.Question.type == q_type)
    if chapter:
        query = query.filter(models.Question.chapter == chapter)
    count = query.count()
    if count == 0:
        return None
    return query.offset(randint(0, count - 1)).limit(1).first()


def check_answer(question: models.Question, user_answer: str) -> bool:
    if question.type == "fill_blank":
        return check_fill_blank_answer(question.answer, user_answer)
    if question.type == "short_answer":
        return check_short_answer_answer(question.answer, user_answer)
    return normalize_answer(user_answer, question.type) == normalize_answer(question.answer, question.type)


def _compute_review_state(
    is_correct: bool,
    current: Optional[models.UserQuestionReview],
    now: datetime,
) -> dict:
    if current is None:
        if is_correct:
            return {
                "review_level": 1,
                "consecutive_correct": 1,
                "consecutive_wrong": 0,
                "next_review_at": now + timedelta(days=_REVIEW_INTERVALS[0]),
                "review_mode": "spaced_repeat",
                "last_reviewed_at": now,
            }
        return {
            "review_level": 0,
            "consecutive_correct": 0,
            "consecutive_wrong": 1,
            "next_review_at": now + timedelta(minutes=10),
            "review_mode": "wrong_review",
            "last_reviewed_at": now,
        }

    if not is_correct:
        return {
            "review_level": 0,
            "consecutive_correct": 0,
            "consecutive_wrong": (current.consecutive_wrong or 0) + 1,
            "next_review_at": now + timedelta(minutes=10),
            "review_mode": "wrong_review",
            "last_reviewed_at": now,
        }

    new_level = min((current.review_level or 0) + 1, 5)
    new_cc = (current.consecutive_correct or 0) + 1
    interval = _REVIEW_INTERVALS[min(new_level - 1, len(_REVIEW_INTERVALS) - 1)]
    return {
        "review_level": new_level,
        "consecutive_correct": new_cc,
        "consecutive_wrong": 0,
        "next_review_at": now + timedelta(days=interval),
        "review_mode": "spaced_repeat",
        "last_reviewed_at": now,
    }


def upsert_user_question_review(
    db: Session,
    user_id: int,
    question_id: int,
    course_id: int | None,
    is_correct: bool,
) -> models.UserQuestionReview:
    now = datetime.now(timezone.utc)

    current = (
        db.query(models.UserQuestionReview)
        .filter(
            models.UserQuestionReview.user_id == user_id,
            models.UserQuestionReview.question_id == question_id,
        )
        .first()
    )

    state = _compute_review_state(is_correct, current, now)

    if current:
        for key, value in state.items():
            setattr(current, key, value)
        current.updated_at = now
        current.course_id = course_id
        record = current
    else:
        record = models.UserQuestionReview(
            user_id=user_id,
            question_id=question_id,
            course_id=course_id,
            **state,
            updated_at=now,
        )
        db.add(record)

    db.flush()
    return record


def get_due_reviews(
    db: Session,
    user_id: int,
    course_id: int | None = None,
    limit: int = 20,
) -> list[models.UserQuestionReview]:
    now = datetime.now(timezone.utc)

    query = (
        db.query(models.UserQuestionReview)
        .filter(models.UserQuestionReview.user_id == user_id)
        .filter(
            (models.UserQuestionReview.next_review_at <= now)
            | (models.UserQuestionReview.next_review_at.is_(None))
        )
    )

    if course_id is not None:
        query = query.filter(models.UserQuestionReview.course_id == course_id)

    query = query.order_by(
        models.UserQuestionReview.next_review_at.asc().nulls_first(),
        models.UserQuestionReview.review_level.asc(),
    )

    return query.limit(limit).all()


def get_user_question_review(
    db: Session, user_id: int, question_id: int,
) -> Optional[models.UserQuestionReview]:
    return (
        db.query(models.UserQuestionReview)
        .filter(
            models.UserQuestionReview.user_id == user_id,
            models.UserQuestionReview.question_id == question_id,
        )
        .first()
    )
