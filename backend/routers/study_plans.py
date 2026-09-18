"""Persisted daily study plans backed by the existing StudyGoal table."""

from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..config import APP_TIMEZONE
from ..database import get_db
from ..services.analytics_service import AnalyticsService

router = APIRouter(prefix="/study-plans", tags=["study-plans"])


def _out(db: Session, goal: models.StudyGoal, user_id: int) -> schemas.StudyPlanOut:
    timezone = ZoneInfo(APP_TIMEZONE)
    today = datetime.now(timezone).date()
    start = datetime.combine(today, time.min, tzinfo=timezone).astimezone(UTC)
    completed = (
        db.query(models.PracticeRecord)
        .filter(models.PracticeRecord.user_id == user_id, models.PracticeRecord.answered_at >= start)
        .count()
    )
    streak = AnalyticsService(db).get_streak(user_id=user_id)["current_streak"]
    target = max(goal.target_count, 1)
    return schemas.StudyPlanOut(
        id=goal.id,
        title=goal.title,
        daily_target=target,
        deadline=goal.deadline.isoformat() if goal.deadline else None,
        today_completed=completed,
        today_remaining=max(target - completed, 0),
        completion_rate=round(min(completed / target, 1) * 100, 2),
        current_streak=streak,
    )


@router.get("/current", response_model=schemas.StudyPlanOut | None)
def current_plan(db: Session = Depends(get_db), current_user=Depends(auth.get_current_user)):
    goal = (
        db.query(models.StudyGoal)
        .filter(models.StudyGoal.user_id == current_user.id)
        .order_by(models.StudyGoal.created_at.desc())
        .first()
    )
    return _out(db, goal, current_user.id) if goal else None


@router.put("/current", response_model=schemas.StudyPlanOut)
def upsert_current_plan(
    body: schemas.StudyPlanUpsert, db: Session = Depends(get_db), current_user=Depends(auth.get_current_user)
):
    goal = (
        db.query(models.StudyGoal)
        .filter(models.StudyGoal.user_id == current_user.id)
        .order_by(models.StudyGoal.created_at.desc())
        .first()
    )
    if goal is None:
        goal = models.StudyGoal(
            user_id=current_user.id, title=body.title.strip(), target_count=body.daily_target, deadline=body.deadline
        )
        db.add(goal)
    else:
        goal.title, goal.target_count, goal.deadline = body.title.strip(), body.daily_target, body.deadline
    db.commit()
    db.refresh(goal)
    return _out(db, goal, current_user.id)
