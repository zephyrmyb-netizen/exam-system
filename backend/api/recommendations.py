"""Recommendation API."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from .. import models, schemas
from ..auth import get_current_user
from ..services.recommendation_service import RecommendationService
from .deps import get_recommendation_service

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

CurrentUser = Annotated[models.User, Depends(get_current_user)]
RecommendationServiceDep = Annotated[RecommendationService, Depends(get_recommendation_service)]


@router.get("/today", response_model=schemas.TodayRecommendationOut)
def today_recommendation(
    current_user: CurrentUser,
    service: RecommendationServiceDep,
):
    return service.get_today_recommendation(user_id=current_user.id)


@router.get("/weak-questions", response_model=list[schemas.QuestionOut])
def weak_questions(
    current_user: CurrentUser,
    service: RecommendationServiceDep,
    limit: int = Query(20, ge=1, le=100),
):
    questions = service.get_weak_questions(user_id=current_user.id, limit=limit)
    return [schemas.QuestionOut.model_validate(question) for question in questions]
