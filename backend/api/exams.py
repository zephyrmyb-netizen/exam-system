"""Layered exam API router."""

import json
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from .. import models, schemas
from ..auth import get_current_user
from ..services.exam_service import ExamService
from .deps import get_exam_service, require_permission

router = APIRouter(prefix="/exams", tags=["exams"])

CurrentUser = Annotated[models.User, Depends(get_current_user)]
ExamServiceDep = Annotated[ExamService, Depends(get_exam_service)]
PageParam = Annotated[int, Query(ge=0)]


def _exam_out(exam: models.Exam) -> schemas.ExamOut:
    return schemas.ExamOut(
        id=exam.id,
        title=exam.title,
        description=exam.description or "",
        course_id=exam.course_id,
        creator_id=exam.creator_id,
        time_limit=exam.time_limit,
        total_score=exam.total_score,
        is_shuffle=bool(exam.is_shuffle),
        is_blind=bool(exam.is_blind),
        status=exam.status,
        question_count=len(exam.questions or []),
        created_at=exam.created_at.isoformat() if exam.created_at else None,
    )


def _question_options(question: models.Question) -> dict[str, str] | None:
    if not question.options:
        return None
    if isinstance(question.options, dict):
        return question.options
    try:
        parsed = json.loads(question.options)
    except (TypeError, json.JSONDecodeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _exam_detail_out(exam: models.Exam) -> schemas.ExamDetailOut:
    base = _exam_out(exam).model_dump()
    questions = sorted(exam.questions or [], key=lambda item: item.order_index)
    return schemas.ExamDetailOut(
        **base,
        questions=[
            schemas.ExamQuestionOut(
                id=exam_question.id,
                question_id=exam_question.question_id,
                question_type=exam_question.question.type,
                question=exam_question.question.question,
                options=_question_options(exam_question.question),
                score=exam_question.score,
                order_index=exam_question.order_index,
            )
            for exam_question in questions
            if exam_question.question is not None
        ],
    )


def _attempt_out(submission: models.ExamSubmission) -> schemas.ExamAttemptOut:
    return schemas.ExamAttemptOut(
        id=submission.id,
        exam_id=submission.exam_id,
        user_id=submission.user_id,
        started_at=submission.started_at.isoformat() if submission.started_at else None,
        submitted_at=submission.submitted_at.isoformat() if submission.submitted_at else None,
        score=submission.score,
    )


@router.post("/", status_code=201, response_model=schemas.ExamOut)
def create_exam(
    body: schemas.ExamCreate,
    current_user: Annotated[models.User, Depends(require_permission("exam:create"))],
    service: ExamServiceDep,
):
    return _exam_out(service.create_exam(body, creator_id=current_user.id))


@router.get("/", response_model=schemas.ExamListOut)
def list_exams(
    service: ExamServiceDep,
    current_user: CurrentUser,
    page: PageParam = 1,
    page_size: PageParam = 20,
):
    exams, total = service.list_published(page=page, page_size=page_size)
    return schemas.ExamListOut(
        items=[_exam_out(exam) for exam in exams],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/mine", response_model=schemas.ExamListOut)
def list_my_exams(
    current_user: CurrentUser,
    service: ExamServiceDep,
    page: PageParam = 1,
    page_size: PageParam = 20,
):
    exams, total = service.list_created(creator_id=current_user.id, page=page, page_size=page_size)
    return schemas.ExamListOut(
        items=[_exam_out(exam) for exam in exams],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{exam_id}", response_model=schemas.ExamDetailOut)
def get_exam_detail(
    exam_id: int,
    current_user: CurrentUser,
    service: ExamServiceDep,
):
    return _exam_detail_out(service.get_detail(exam_id, current_user.id))


@router.post("/{exam_id}/publish", response_model=schemas.ExamOut)
def publish_exam(
    exam_id: int,
    current_user: Annotated[models.User, Depends(require_permission("exam:publish"))],
    service: ExamServiceDep,
):
    return _exam_out(service.publish_exam(exam_id, current_user.id))


@router.post("/{exam_id}/start", response_model=schemas.ExamAttemptOut)
def start_exam(
    exam_id: int,
    current_user: CurrentUser,
    service: ExamServiceDep,
):
    return _attempt_out(service.start_attempt(exam_id, current_user.id))


@router.post("/{exam_id}/submit", response_model=schemas.ExamResultOut)
def submit_exam(
    exam_id: int,
    body: schemas.ExamSubmissionCreate,
    current_user: CurrentUser,
    service: ExamServiceDep,
):
    return service.submit_exam(exam_id, current_user.id, body)
