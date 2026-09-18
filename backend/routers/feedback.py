"""Authenticated help and feedback submission API."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db

router = APIRouter(prefix="/feedback", tags=["feedback"])
CurrentUser = Annotated[models.User, Depends(auth.get_current_user)]


def _feedback_out(entry: models.FeedbackEntry) -> schemas.FeedbackOut:
    return schemas.FeedbackOut(
        id=entry.id,
        category=entry.category,
        content=entry.content,
        contact=entry.contact,
        created_at=entry.created_at.isoformat() if entry.created_at else None,
    )


@router.post("/", response_model=schemas.FeedbackOut, status_code=status.HTTP_201_CREATED)
def create_feedback(
    body: schemas.FeedbackCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    entry = models.FeedbackEntry(
        user_id=current_user.id,
        category=body.category,
        content=body.content,
        contact=body.contact,
        created_at=datetime.now(UTC),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return _feedback_out(entry)
