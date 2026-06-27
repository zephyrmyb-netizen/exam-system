import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from . import models, schemas
from .config import APP_TIMEZONE


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


def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, user_in: schemas.UserCreate, password_hash: str) -> models.User:
    user = models.User(username=user_in.username, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _add_question_visibility_filter(query, user_id: int | None):
    """Filter questions so the caller can see them."""
    from sqlalchemy import or_

    if user_id is not None:
        return query.filter(
            or_(
                models.Question.visibility == "public",
                models.Question.owner_id == user_id,
                models.Question.owner_id.is_(None),
            )
        )
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


def derive_course_name_from_filename(filename: str) -> str:
    """Convert an uploaded filename to a suggested question-bank name."""
    if not filename:
        return "未分类题库"

    name = Path(filename).stem if filename else filename
    name = name.strip()
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r'[\\/:*?"<>|]', "", name)

    if not name or not name.strip():
        return "未分类题库"

    name = name[:80].strip()
    return name if name else "未分类题库"


def apply_pagination(query, page: int, page_size: int):
    """Apply offset/limit pagination to a SQLAlchemy query.

    Returns (items, total). When page or page_size <= 0, returns all rows.
    """
    total = query.count()
    if page > 0 and page_size > 0:
        query = query.offset((page - 1) * page_size).limit(page_size)
    return query.all(), total
