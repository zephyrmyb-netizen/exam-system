"""Analytics API: personal and owner views."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from .. import models, schemas
from ..auth import get_current_user
from ..services.analytics_service import AnalyticsService
from .deps import get_analytics_service, require_permission

router = APIRouter(prefix="/analytics", tags=["analytics"])

CurrentUser = Annotated[models.User, Depends(get_current_user)]
AnalyticsServiceDep = Annotated[AnalyticsService, Depends(get_analytics_service)]


@router.get("/daily-activity", response_model=list[schemas.DailyActivityOut])
def daily_activity(
    current_user: CurrentUser,
    service: AnalyticsServiceDep,
    days: int = Query(30, ge=1, le=365),
):
    return service.get_daily_activity(user_id=current_user.id, days=days)


@router.get("/type-distribution", response_model=list[schemas.TypeDistributionOut])
def type_distribution(
    current_user: CurrentUser,
    service: AnalyticsServiceDep,
):
    return service.get_type_distribution(user_id=current_user.id)


@router.get("/streak", response_model=schemas.StreakOut)
def streak(
    current_user: CurrentUser,
    service: AnalyticsServiceDep,
):
    return service.get_streak(user_id=current_user.id)


@router.get("/owner/courses", response_model=list[schemas.CourseAnalyticsOut])
def owner_courses(
    service: AnalyticsServiceDep,
    current_user: models.User = Depends(require_permission("course:read")),
):
    return service.get_course_stats_for_owner(owner_id=current_user.id)


@router.get("/owner/exam-scores/{exam_id}", response_model=list[schemas.ScoreBucketOut])
def owner_exam_scores(
    exam_id: int,
    service: AnalyticsServiceDep,
    current_user: models.User = Depends(require_permission("exam:view_leaderboard")),
):
    return service.get_score_distribution(exam_id=exam_id)


@router.get("/owner/exams/{exam_id}", response_model=schemas.ExamAnalyticsOut)
def owner_exam_analysis(
    exam_id: int,
    service: AnalyticsServiceDep,
    current_user: CurrentUser,
):
    return service.get_exam_analysis(exam_id=exam_id, owner_id=current_user.id)
