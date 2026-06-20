import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models, schemas
from .config import APP_TIMEZONE
from .utils import normalize_answer, check_fill_blank_answer, check_short_answer_answer


# ── Timezone ────────────────────────────────────────────────────────────────

def _local_now() -> datetime:
    """Return current datetime in the configured timezone (naive, for comparison)."""
    from zoneinfo import ZoneInfo
    tz = ZoneInfo(APP_TIMEZONE)
    return datetime.now(tz).replace(tzinfo=None)


def _local_today_start() -> datetime:
    """Return the start of today in the configured timezone (naive)."""
    return _local_now().replace(hour=0, minute=0, second=0, microsecond=0)


def _utc_to_local(dt: datetime) -> datetime:
    """Convert a timezone-aware UTC datetime to the configured timezone (naive)."""
    from zoneinfo import ZoneInfo
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    tz = ZoneInfo(APP_TIMEZONE)
    return dt.astimezone(tz).replace(tzinfo=None)


# ── User ────────────────────────────────────────────────────────────────────

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, user_in: schemas.UserCreate, password_hash: str) -> models.User:
    user = models.User(username=user_in.username, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ── Visibility helpers ──────────────────────────────────────────────────────

def _add_question_visibility_filter(query, user_id: int | None):
    """Filter questions so the caller can see them.

    Rules:
    - visibility='public' → visible to everyone
    - visibility='private' → only visible to owner
    - owner_id IS NULL → backward compat: treat as visible to everyone
    """
    from sqlalchemy import or_
    if user_id is not None:
        return query.filter(
            or_(
                models.Question.visibility == "public",
                models.Question.owner_id == user_id,
                models.Question.owner_id.is_(None),
            )
        )
    # unauthenticated (shouldn't happen in practice, but be safe)
    return query.filter(models.Question.visibility == "public")


def _add_bank_visibility_filter(query, user_id: int | None):
    """Filter question banks so the caller can see them."""
    from sqlalchemy import or_
    if user_id is not None:
        return query.filter(
            or_(
                models.QuestionBank.visibility == "public",
                models.QuestionBank.owner_id == user_id,
            )
        )
    return query.filter(models.QuestionBank.visibility == "public")


# ── Utility: derive course name from filename ──────────────────────────────

def derive_course_name_from_filename(filename: str) -> str:
    """Convert an uploaded filename to a suggested question-bank name.

    Rules:
    1. Remove the extension (.docx, .pptx, etc.)
    2. Strip leading/trailing whitespace
    3. Collapse consecutive whitespace into one space
    4. Filter characters that are illegal on most filesystems: \\ / : * ? " < > |
    5. Empty fallback → "未分类题库"
    6. Truncate to 80 chars

    Examples:
      "java复习题.docx"     → "java复习题"
      "  期末 考试 题.pptx " → "期末 考试 题"
      ""                     → "未分类题库"
    """
    if not filename:
        return "未分类题库"

    # Strip extension
    name = Path(filename).stem if filename else filename

    # Strip whitespace
    name = name.strip()

    # Collapse consecutive whitespace
    name = re.sub(r'\s+', ' ', name)

    # Filter illegal filename characters
    name = re.sub(r'[\\/:*?"<>|]', '', name)

    # Empty after filtering
    if not name or not name.strip():
        return "未分类题库"

    # Truncate
    name = name[:80].strip()

    return name if name else "未分类题库"


# ── Question Bank ───────────────────────────────────────────────────────────

def create_question_bank(
    db: Session, bank_in: schemas.CourseCreate, owner_id: int
) -> models.QuestionBank:
    bank = models.QuestionBank(
        owner_id=owner_id,
        name=bank_in.name,
        description=bank_in.description,
        subject=bank_in.subject,
        visibility=bank_in.visibility,
        created_at=datetime.now(timezone.utc),
    )
    db.add(bank)
    db.commit()
    db.refresh(bank)
    return bank


def get_or_create_uncategorized_bank(db: Session, user_id: int) -> models.QuestionBank:
    """Find the user's 'Uncategorized' bank or create one."""
    bank = (
        db.query(models.QuestionBank)
        .filter(models.QuestionBank.owner_id == user_id, models.QuestionBank.name == "未分类题库")
        .first()
    )
    if bank:
        return bank
    bank = models.QuestionBank(
        owner_id=user_id,
        name="未分类题库",
        description="自动创建的默认题库",
        visibility="private",
        created_at=datetime.now(timezone.utc),
    )
    db.add(bank)
    db.commit()
    db.refresh(bank)
    return bank


def resolve_course(
    db: Session,
    user_id: int,
    course_id: int | None = None,
    course_name: str | None = None,
) -> tuple[models.QuestionBank, bool]:
    """Resolve course_id → QuestionBank, or course_name → find-or-create, or fallback.

    Priority:
    1. If course_id is given, verify it belongs to the user.
    2. Elif course_name is non-empty: find bank with that name owned by user, or create one.
    3. Otherwise: auto-create (or return) the default "未分类题库" bank.
    Returns (bank, was_created).
    """
    if course_id is not None:
        bank = db.query(models.QuestionBank).filter(models.QuestionBank.id == course_id).first()
        if not bank:
            raise ValueError(f"课程（题库）不存在: course_id={course_id}")
        if bank.owner_id != user_id:
            raise ValueError("无权使用此课程（题库）")
        return bank, False

    name = (course_name or "").strip()
    if name:
        # Find-or-create by name for this user
        bank = (
            db.query(models.QuestionBank)
            .filter(models.QuestionBank.owner_id == user_id, models.QuestionBank.name == name)
            .first()
        )
        if bank:
            return bank, False
        bank = models.QuestionBank(
            owner_id=user_id,
            name=name,
            description=f"从文件导入: {name}",
            visibility="private",
            created_at=datetime.now(timezone.utc),
        )
        db.add(bank)
        db.commit()
        db.refresh(bank)
        return bank, True

    # Fallback — uncategorized
    bank = get_or_create_uncategorized_bank(db, user_id)
    return bank, True


def get_question_banks(
    db: Session, user_id: int | None, page: int = 0, page_size: int = 0,
) -> tuple[list[models.QuestionBank], int]:
    query = _add_bank_visibility_filter(db.query(models.QuestionBank), user_id)
    total = query.count()
    query = query.order_by(models.QuestionBank.created_at.desc())
    if page > 0 and page_size > 0:
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
    return query.all(), total


def get_my_question_banks(
    db: Session, user_id: int, page: int = 0, page_size: int = 0,
) -> tuple[list[models.QuestionBank], int]:
    """Return only the current user's own question banks (private or public).

    Eagerly loads the questions relationship so question_count is O(1).
    """
    from sqlalchemy.orm import selectinload

    query = (
        db.query(models.QuestionBank)
        .filter(models.QuestionBank.owner_id == user_id)
        .options(selectinload(models.QuestionBank.questions))
    )
    total = query.count()
    query = query.order_by(models.QuestionBank.created_at.desc())
    if page > 0 and page_size > 0:
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
    return query.all(), total


def get_public_question_banks(
    db: Session,
    page: int = 0,
    page_size: int = 0,
    keyword: str = "",
    subject: str = "",
) -> tuple[list[models.QuestionBank], int]:
    """Return only public question banks (the public library).

    Supports keyword search on name, description, and subject;
    and exact subject filter.
    """
    from sqlalchemy import or_

    query = db.query(models.QuestionBank).filter(models.QuestionBank.visibility == "public")

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(
                models.QuestionBank.name.like(like),
                models.QuestionBank.description.like(like),
                models.QuestionBank.subject.like(like),
            )
        )
    if subject:
        query = query.filter(models.QuestionBank.subject == subject)

    total = query.count()
    query = query.order_by(models.QuestionBank.created_at.desc())

    if page > 0 and page_size > 0:
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

    return query.all(), total


def get_question_bank_by_id(db: Session, bank_id: int) -> Optional[models.QuestionBank]:
    return db.query(models.QuestionBank).filter(models.QuestionBank.id == bank_id).first()


def delete_question_bank(db: Session, bank_id: int) -> bool:
    """Delete a question bank and all its questions.

    Also cleans up related data:
    - wrong_records are cascade-deleted with questions (via ORM cascade)
    - practice_records keep their history but course_id/question_id are nullified
    - user_question_reviews are nullified
    """
    bank = db.query(models.QuestionBank).filter(models.QuestionBank.id == bank_id).first()
    if not bank:
        return False

    # Collect question IDs before cascade destroys them
    question_ids = [
        row[0] for row in
        db.query(models.Question.id).filter(models.Question.course_id == bank_id).all()
    ]

    if question_ids:
        # Nullify practice_records pointing to these questions or this course
        db.query(models.PracticeRecord).filter(
            models.PracticeRecord.question_id.in_(question_ids)
        ).update({"question_id": None}, synchronize_session=False)
        db.query(models.PracticeRecord).filter(
            models.PracticeRecord.course_id == bank_id
        ).update({"course_id": None}, synchronize_session=False)

        # Nullify user_question_reviews
        db.query(models.UserQuestionReview).filter(
            models.UserQuestionReview.question_id.in_(question_ids)
        ).update({"question_id": None}, synchronize_session=False)
        db.query(models.UserQuestionReview).filter(
            models.UserQuestionReview.course_id == bank_id
        ).update({"course_id": None}, synchronize_session=False)

    # Delete the bank — ORM cascade deletes questions, which cascade-deletes wrong_records
    db.delete(bank)
    db.commit()
    return True


def update_question_bank_visibility(
    db: Session, bank_id: int, visibility: str
) -> Optional[models.QuestionBank]:
    bank = db.query(models.QuestionBank).filter(models.QuestionBank.id == bank_id).first()
    if not bank:
        return None
    bank.visibility = visibility
    db.commit()
    db.refresh(bank)
    return bank


def update_question_bank(
    db: Session, bank_id: int, data: schemas.CourseUpdate,
) -> Optional[models.QuestionBank]:
    """Update a course's name, description, and/or subject."""
    bank = db.query(models.QuestionBank).filter(models.QuestionBank.id == bank_id).first()
    if not bank:
        return None
    if data.name is not None:
        if not data.name.strip():
            raise ValueError("课程名称不能为空")
        bank.name = data.name.strip()
    if data.description is not None:
        bank.description = data.description
    if data.subject is not None:
        bank.subject = data.subject
    db.commit()
    db.refresh(bank)
    return bank


# ── Question ────────────────────────────────────────────────────────────────

def get_questions(
    db: Session,
    user_id: int | None = None,
    page: int = 0,
    page_size: int = 0,
    keyword: str = "",
    subject: str = "",
    chapter: str = "",
    q_type: str = "",
    course_id: int | None = None,
) -> tuple[list[models.Question], int]:
    """Get questions with optional filtering and pagination.

    When page=0 or page_size=0, returns all matching questions (legacy mode).
    Returns (questions_list, total_count).
    """
    query = _add_question_visibility_filter(db.query(models.Question), user_id)

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(models.Question.question.like(like))
    if subject:
        query = query.filter(models.Question.subject == subject)
    if chapter:
        query = query.filter(models.Question.chapter == chapter)
    if q_type:
        query = query.filter(models.Question.type == q_type)
    if course_id is not None:
        query = query.filter(models.Question.course_id == course_id)

    total = query.count()
    query = query.order_by(models.Question.id.desc())

    if page > 0 and page_size > 0:
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

    return query.all(), total


def get_question_by_id(db: Session, question_id: int) -> Optional[models.Question]:
    return db.query(models.Question).filter(models.Question.id == question_id).first()


def get_visible_question_by_id(db: Session, question_id: int, user_id: int) -> Optional[models.Question]:
    """Get a question by ID, but only if it is visible to the given user."""
    query = _add_question_visibility_filter(
        db.query(models.Question).filter(models.Question.id == question_id),
        user_id,
    )
    return query.first()


def create_questions_batch(
    db: Session,
    questions_data: list[schemas.QuestionCreate],
    owner_id: int,
    course_id: int | None = None,
    visibility: str = "private",
    source: str = "import",
) -> int:
    count = 0
    for q in questions_data:
        normalized_answer = normalize_answer(q.answer, q.type)
        # Use batch-level course_id if given, otherwise per-question course_id
        q_course_id = course_id if course_id is not None else q.course_id
        question = models.Question(
            owner_id=owner_id,
            course_id=q_course_id,
            visibility=visibility,
            source=source,
            created_at=datetime.now(timezone.utc),
            subject=q.subject,
            chapter=q.chapter,
            type=q.type,
            question=q.question,
            answer=normalized_answer,
            analysis=q.analysis or "",
            difficulty=q.difficulty or "normal",
        )
        question.set_options_dict(q.options)
        db.add(question)
        count += 1
    db.commit()
    return count


def delete_question(db: Session, question_id: int) -> bool:
    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not question:
        return False
    db.delete(question)
    db.commit()
    return True


def create_single_question(
    db: Session, data: schemas.QuestionManualCreate, owner_id: int,
) -> models.Question:
    """Create a single question manually (source=manual)."""
    normalized_answer = normalize_answer(data.answer, data.type)
    question = models.Question(
        owner_id=owner_id,
        course_id=data.course_id,
        visibility="private",
        source="manual",
        created_at=datetime.now(timezone.utc),
        subject=data.subject,
        chapter=data.chapter,
        type=data.type,
        question=data.question,
        answer=normalized_answer,
        analysis=data.analysis or "",
        difficulty=data.difficulty or "normal",
    )
    question.set_options_dict(data.options)
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def update_question(
    db: Session, question_id: int, data: schemas.QuestionUpdate,
) -> Optional[models.Question]:
    """Update a question's fields. Only sets fields that are not None."""
    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not question:
        return None

    if data.subject is not None:
        question.subject = data.subject
    if data.chapter is not None:
        question.chapter = data.chapter
    if data.type is not None:
        question.type = data.type
    if data.question is not None:
        if not data.question.strip():
            raise ValueError("题目题干不能为空")
        question.question = data.question.strip()
    if data.options is not None:
        question.set_options_dict(data.options)
    if data.answer is not None:
        question.answer = data.answer  # already normalized by schema validator
    if data.analysis is not None:
        question.analysis = data.analysis
    if data.difficulty is not None:
        question.difficulty = data.difficulty
    if data.course_id is not None:
        question.course_id = data.course_id

    # Validate consistency: if type changed to choice, must have options
    q_type = question.type
    if q_type in ("single_choice", "multiple_choice") and not question.options:
        raise ValueError("选择题（single_choice / multiple_choice）必须提供 options")
    # Re-normalize answer if type was changed
    if data.type is not None and data.answer is not None:
        question.answer = normalize_answer(question.answer, question.type)

    db.commit()
    db.refresh(question)
    return question


def update_question_visibility(
    db: Session, question_id: int, visibility: str
) -> Optional[models.Question]:
    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not question:
        return None
    question.visibility = visibility
    db.commit()
    db.refresh(question)
    return question


def get_public_questions(
    db: Session,
    page: int = 0,
    page_size: int = 0,
    keyword: str = "",
    subject: str = "",
    chapter: str = "",
    q_type: str = "",
    course_id: int | None = None,
) -> tuple[list[models.Question], int]:
    """Get only public questions (for the public library browsing)."""
    query = db.query(models.Question).filter(models.Question.visibility == "public")

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(models.Question.question.like(like))
    if subject:
        query = query.filter(models.Question.subject == subject)
    if chapter:
        query = query.filter(models.Question.chapter == chapter)
    if q_type:
        query = query.filter(models.Question.type == q_type)
    if course_id is not None:
        query = query.filter(models.Question.course_id == course_id)

    total = query.count()
    query = query.order_by(models.Question.id.desc())

    if page > 0 and page_size > 0:
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

    return query.all(), total


def get_my_questions(
    db: Session,
    user_id: int,
    page: int = 0,
    page_size: int = 0,
    keyword: str = "",
    subject: str = "",
    chapter: str = "",
    q_type: str = "",
    course_id: int | None = None,
) -> tuple[list[models.Question], int]:
    """Get only the current user's own questions, regardless of visibility."""
    query = db.query(models.Question).filter(models.Question.owner_id == user_id)

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(models.Question.question.like(like))
    if subject:
        query = query.filter(models.Question.subject == subject)
    if chapter:
        query = query.filter(models.Question.chapter == chapter)
    if q_type:
        query = query.filter(models.Question.type == q_type)
    if course_id is not None:
        query = query.filter(models.Question.course_id == course_id)

    total = query.count()
    query = query.order_by(models.Question.id.desc())

    if page > 0 and page_size > 0:
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

    return query.all(), total


# ── Practice ────────────────────────────────────────────────────────────────

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
    """Record every answer attempt (correct or incorrect).
    
    Note: does NOT call db.commit() — the caller is responsible for
    committing the transaction so that practice record, wrong record,
    and review state are all written atomically.
    """
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
    """Return practice statistics for the given user.

    today_count uses the configured APP_TIMEZONE (default Asia/Shanghai),
    not UTC.
    """
    from zoneinfo import ZoneInfo

    now_utc = datetime.now(timezone.utc)
    local_tz = ZoneInfo(APP_TIMEZONE)
    local_midnight = datetime.now(local_tz).replace(hour=0, minute=0, second=0, microsecond=0)
    # Convert local midnight to UTC for comparison with answered_at (UTC)
    today_start = local_midnight.astimezone(timezone.utc)
    seven_days_ago = now_utc - timedelta(days=7)

    base = db.query(models.PracticeRecord).filter(models.PracticeRecord.user_id == user_id)

    total_count = base.count()
    if total_count == 0:
        return {
            "today_count": 0,
            "total_count": 0,
            "correct_count": 0,
            "wrong_count": 0,
            "accuracy_rate": 0.0,
            "recent_count_7d": 0,
        }

    correct_count = base.filter(models.PracticeRecord.is_correct == 1).count()
    wrong_count = total_count - correct_count
    today_count = base.filter(models.PracticeRecord.answered_at >= today_start).count()
    recent_count_7d = base.filter(models.PracticeRecord.answered_at >= seven_days_ago).count()
    accuracy_rate = round(correct_count / total_count, 4) if total_count > 0 else 0.0

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
    """Return paginated practice records for a user, newest first."""
    from sqlalchemy.orm import joinedload

    query = (
        db.query(models.PracticeRecord)
        .filter(models.PracticeRecord.user_id == user_id)
        .options(joinedload(models.PracticeRecord.question))
    )
    total = query.count()
    query = query.order_by(models.PracticeRecord.answered_at.desc())
    if page > 0 and page_size > 0:
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
    return query.all(), total


def get_practice_stats_by_course(
    db: Session, user_id: int, course_ids: list[int],
) -> dict[int, dict]:
    """Return per-course practice stats for the given user and courses.

    Returns a dict mapping course_id → {practice_count, last_practiced_at}.
    Only includes courses that have at least one practice record.
    """
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
    """Return today's review suggestion based on due reviews, wrong records, and practice history.

    due_count: count of actually due review records (next_review_at <= now).
    wrong_count: total wrong records count.
    weak_types: question types with >50% error rate in recent practice.
    recommended_modes: practice modes suggested based on available data.
    """
    now = datetime.now(timezone.utc)

    # Due count from UserQuestionReview (spaced repetition)
    due_count = (
        db.query(models.UserQuestionReview)
        .filter(models.UserQuestionReview.user_id == user_id)
        .filter(
            (models.UserQuestionReview.next_review_at <= now)
            | (models.UserQuestionReview.next_review_at.is_(None))
        )
        .count()
    )

    # Wrong record counts
    wrong_base = db.query(models.WrongRecord).filter(models.WrongRecord.user_id == user_id)
    wrong_count = wrong_base.count()

    # Weak types from recent practice (last 50 records)
    recent = (
        db.query(models.PracticeRecord)
        .filter(models.PracticeRecord.user_id == user_id)
        .order_by(models.PracticeRecord.answered_at.desc())
        .limit(50)
        .all()
    )

    # Group by question_type
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
            if error_rate >= 0.4:  # 40%+ error rate considered weak
                weak_types.append({
                    "question_type": qt,
                    "total_attempts": stats["total"],
                    "wrong_attempts": stats["wrong"],
                    "error_rate": error_rate,
                })

    # Sort by error rate descending
    weak_types.sort(key=lambda x: x["error_rate"], reverse=True)

    # Recommended modes
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
    """Analyze weak question types from the user's recent practice records.

    Returns types with above-average error rate, sorted by error_rate desc.
    """
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

    # Overall error rate
    total_attempts = sum(s["total"] for s in type_stats.values())
    total_wrong = sum(s["wrong"] for s in type_stats.values())
    overall_rate = total_wrong / total_attempts if total_attempts > 0 else 0

    weak_types = []
    for qt, stats in type_stats.items():
        if stats["total"] >= 2:  # at least 2 attempts to be meaningful
            rate = round(stats["wrong"] / stats["total"], 4)
            # Include if rate > overall average
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
    query = _add_question_visibility_filter(db.query(models.Question), user_id)
    if q_type:
        query = query.filter(models.Question.type == q_type)
    if chapter:
        query = query.filter(models.Question.chapter == chapter)
    return query.order_by(func.random()).first()


def get_random_question_in_course(
    db: Session, course_id: int, user_id: int | None = None, q_type: str = "", chapter: str = "",
) -> Optional[models.Question]:
    """Get a random question from a specific course, respecting visibility rules."""
    query = _add_question_visibility_filter(
        db.query(models.Question).filter(models.Question.course_id == course_id),
        user_id,
    )
    if q_type:
        query = query.filter(models.Question.type == q_type)
    if chapter:
        query = query.filter(models.Question.chapter == chapter)
    return query.order_by(func.random()).first()


def get_random_wrong_question(
    db: Session, user_id: int, course_id: int | None = None, q_type: str = "",
) -> Optional[models.Question]:
    """Get a random question from the user's wrong records, prioritizing high wrong_count.

    Only returns questions that are still visible to the user.
    """
    from sqlalchemy.orm import joinedload

    # Subquery: get question_ids from user's wrong_records
    wrong_qids = (
        db.query(models.WrongRecord.question_id)
        .filter(models.WrongRecord.user_id == user_id)
    )

    query = _add_question_visibility_filter(
        db.query(models.Question).filter(models.Question.id.in_(wrong_qids)),
        user_id,
    )

    if course_id is not None:
        query = query.filter(models.Question.course_id == course_id)
    if q_type:
        query = query.filter(models.Question.type == q_type)

    # Join wrong_records to order by wrong_count desc
    query = (
        query.join(models.WrongRecord, models.WrongRecord.question_id == models.Question.id)
        .filter(models.WrongRecord.user_id == user_id)
        .order_by(models.WrongRecord.wrong_count.desc(), func.random())
    )

    return query.first()


def check_answer(question: models.Question, user_answer: str) -> bool:
    """Compare user answer with question.answer using type-aware normalization.

    fill_blank: supports || for multiple acceptable answers
    short_answer: supports && (all keywords) and || (any alternative)
    """
    if question.type == "fill_blank":
        return check_fill_blank_answer(question.answer, user_answer)
    if question.type == "short_answer":
        return check_short_answer_answer(question.answer, user_answer)
    return normalize_answer(user_answer, question.type) == normalize_answer(question.answer, question.type)


# ── Spaced Repetition Review ──────────────────────────────────────────────

_REVIEW_INTERVALS = [1, 3, 7, 14, 30]  # days at each level


def _compute_review_state(
    is_correct: bool,
    current: Optional[models.UserQuestionReview],
    now: datetime,
) -> dict:
    """Compute the next review state for a user-question pair.

    Returns a dict with keys matching UserQuestionReview columns.
    """
    if current is None:
        # First time seeing this question
        if is_correct:
            return {
                "review_level": 1,
                "consecutive_correct": 1,
                "consecutive_wrong": 0,
                "next_review_at": now + timedelta(days=_REVIEW_INTERVALS[0]),
                "review_mode": "spaced_repeat",
                "last_reviewed_at": now,
            }
        else:
            return {
                "review_level": 0,
                "consecutive_correct": 0,
                "consecutive_wrong": 1,
                "next_review_at": now + timedelta(minutes=10),
                "review_mode": "wrong_review",
                "last_reviewed_at": now,
            }

    if not is_correct:
        # Wrong answer: reset
        return {
            "review_level": 0,
            "consecutive_correct": 0,
            "consecutive_wrong": (current.consecutive_wrong or 0) + 1,
            "next_review_at": now + timedelta(minutes=10),
            "review_mode": "wrong_review",
            "last_reviewed_at": now,
        }

    # Correct answer
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
    """Create or update the review state for a user-question pair after answering."""
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
    """Return review records that are due for the user.

    A record is due when next_review_at is NULL or in the past.
    Ordered by next_review_at ASC (earliest first), then review_level ASC (low level first).
    """
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
    """Get the review state for a single user-question pair."""
    return (
        db.query(models.UserQuestionReview)
        .filter(
            models.UserQuestionReview.user_id == user_id,
            models.UserQuestionReview.question_id == question_id,
        )
        .first()
    )


# ── Wrong Record ────────────────────────────────────────────────────────────

def get_wrong_records(
    db: Session,
    user_id: int,
    page: int = 0,
    page_size: int = 0,
    keyword: str = "",
    subject: str = "",
    chapter: str = "",
    q_type: str = "",
) -> tuple[list[models.WrongRecord], int]:
    """Get wrong records with optional filtering by question fields and pagination.

    When page=0 or page_size=0, returns all matching records (legacy mode).
    Returns (records_list, total_count).
    """
    query = (
        db.query(models.WrongRecord)
        .filter(models.WrongRecord.user_id == user_id)
        .join(models.Question)
    )

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(models.Question.question.like(like))
    if subject:
        query = query.filter(models.Question.subject == subject)
    if chapter:
        query = query.filter(models.Question.chapter == chapter)
    if q_type:
        query = query.filter(models.Question.type == q_type)

    total = query.count()
    query = query.order_by(models.WrongRecord.id.desc())

    if page > 0 and page_size > 0:
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

    return query.all(), total


def upsert_wrong_record(db: Session, user_id: int, question_id: int, user_answer: str) -> models.WrongRecord:
    record = (
        db.query(models.WrongRecord)
        .filter(models.WrongRecord.user_id == user_id, models.WrongRecord.question_id == question_id)
        .first()
    )
    if record:
        record.wrong_count += 1
        record.last_wrong_answer = user_answer
    else:
        record = models.WrongRecord(
            user_id=user_id,
            question_id=question_id,
            wrong_count=1,
            last_wrong_answer=user_answer,
        )
        db.add(record)
    db.flush()
    return record


def delete_wrong_record(db: Session, user_id: int, question_id: int) -> bool:
    record = (
        db.query(models.WrongRecord)
        .filter(models.WrongRecord.user_id == user_id, models.WrongRecord.question_id == question_id)
        .first()
    )
    if not record:
        return False
    db.delete(record)
    db.commit()
    return True


def clear_wrong_record_if_correct(db: Session, user_id: int, question_id: int) -> None:
    """If the user answered correctly, remove the wrong record if it exists.

    Note: does NOT call db.commit() — the caller is responsible for
    committing the transaction so that wrong record, practice record,
    and review state are all written atomically.
    """
    record = (
        db.query(models.WrongRecord)
        .filter(models.WrongRecord.user_id == user_id, models.WrongRecord.question_id == question_id)
        .first()
    )
    if record:
        db.delete(record)
        db.flush()


# -- Metadata -----------------------------------------------------------------

def get_question_meta(db: Session, user_id: int | None = None) -> dict:
    """Get distinct subjects and chapters across visible questions for filter dropdowns."""
    query = _add_question_visibility_filter(
        db.query(models.Question).distinct(), user_id
    )
    subjects = [
        r[0] for r in query.with_entities(models.Question.subject)
        .distinct().order_by(models.Question.subject).all()
        if r[0]
    ]
    chapters = [
        r[0] for r in query.with_entities(models.Question.chapter)
        .distinct().order_by(models.Question.chapter).all()
        if r[0]
    ]
    return {"subjects": subjects, "chapters": chapters}


def get_wrongbook_meta(db: Session, user_id: int) -> dict:
    """Get distinct subjects and chapters from questions in user's wrong records."""
    subjects = [
        r[0] for r in db.query(models.Question.subject)
        .join(models.WrongRecord)
        .filter(models.WrongRecord.user_id == user_id)
        .distinct().order_by(models.Question.subject).all()
        if r[0]
    ]
    chapters = [
        r[0] for r in db.query(models.Question.chapter)
        .join(models.WrongRecord)
        .filter(models.WrongRecord.user_id == user_id)
        .distinct().order_by(models.Question.chapter).all()
        if r[0]
    ]
    return {"subjects": subjects, "chapters": chapters}
