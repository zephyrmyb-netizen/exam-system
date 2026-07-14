"""Knowledge tag API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from .. import crud, models, schemas
from ..auth import get_current_user
from ..services.tag_service import TagService
from .deps import get_tag_service

router = APIRouter(prefix="/tags", tags=["tags"])

CurrentUser = Annotated[models.User, Depends(get_current_user)]
TagServiceDep = Annotated[TagService, Depends(get_tag_service)]


def _tag_out(tag: models.Tag) -> schemas.TagOut:
    return schemas.TagOut.model_validate(tag)


def _owned_question(question_id: int, user_id: int, service: TagService) -> models.Question:
    question = crud.get_question_by_id(service.db, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if question.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Only the owner can tag this question")
    return question


@router.get("/", response_model=schemas.TagListOut)
def list_tags(
    current_user: CurrentUser,
    service: TagServiceDep,
    keyword: str = Query("", description="Search keyword"),
    page: int = Query(0, ge=0),
    page_size: int = Query(0, ge=0),
):
    tags, total = service.list_tags(keyword=keyword, page=page, page_size=page_size)
    return schemas.TagListOut(
        items=[_tag_out(tag) for tag in tags],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/", status_code=201, response_model=schemas.TagOut)
def create_tag(
    body: schemas.TagCreate,
    current_user: CurrentUser,
    service: TagServiceDep,
):
    try:
        return _tag_out(service.create_tag(name=body.name, color=body.color, parent_id=body.parent_id))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/accuracy", response_model=list[schemas.TagAccuracyOut])
def get_tag_accuracy(
    current_user: CurrentUser,
    service: TagServiceDep,
):
    return service.get_accuracy_by_tag(user_id=current_user.id)


@router.get("/questions/{question_id}", response_model=list[schemas.TagOut])
def list_question_tags(
    question_id: int,
    current_user: CurrentUser,
    service: TagServiceDep,
):
    _owned_question(question_id, current_user.id, service)
    return [_tag_out(tag) for tag in service.list_question_tags(question_id)]


@router.post("/questions/{question_id}", response_model=list[schemas.TagOut])
def tag_question(
    question_id: int,
    body: schemas.QuestionTagAssign,
    current_user: CurrentUser,
    service: TagServiceDep,
):
    _owned_question(question_id, current_user.id, service)
    return [_tag_out(tag) for tag in service.replace_question_tags(question_id=question_id, tag_names=body.tag_names)]
