"""Personal question bookmark API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from .. import models, schemas
from ..auth import get_current_user
from ..repositories import BookmarkRepository
from .deps import DbSession, get_bookmark_repo

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])

CurrentUser = Annotated[models.User, Depends(get_current_user)]
BookmarkRepoDep = Annotated[BookmarkRepository, Depends(get_bookmark_repo)]


def _visible_question_or_404(db: DbSession, *, question_id: int, user_id: int) -> models.Question:
    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    if question.owner_id != user_id and question.visibility != "public":
        raise HTTPException(status_code=404, detail="Question not found")
    return question


def _bookmark_out(bookmark: models.Bookmark) -> schemas.BookmarkOut:
    return schemas.BookmarkOut.model_validate(bookmark)


@router.post("/", status_code=201, response_model=schemas.BookmarkOut)
def add_bookmark(
    body: schemas.BookmarkCreate,
    current_user: CurrentUser,
    repo: BookmarkRepoDep,
    db: DbSession,
):
    _visible_question_or_404(db, question_id=body.question_id, user_id=current_user.id)
    bookmark = repo.upsert(
        user_id=current_user.id,
        question_id=body.question_id,
        folder_name=body.folder_name.strip() or "Default",
        note=body.note.strip(),
    )
    return _bookmark_out(bookmark)


@router.get("/", response_model=schemas.BookmarkListOut)
def list_bookmarks(
    current_user: CurrentUser,
    repo: BookmarkRepoDep,
    folder: str = Query("", description="Optional bookmark folder name"),
):
    items, total = repo.list_for_user(user_id=current_user.id, folder=folder.strip())
    return schemas.BookmarkListOut(
        items=[_bookmark_out(item) for item in items],
        total=total,
        folders=repo.list_folders_for_user(user_id=current_user.id),
    )


@router.delete("/{question_id}")
def remove_bookmark(
    question_id: int,
    current_user: CurrentUser,
    repo: BookmarkRepoDep,
):
    repo.delete_for_user_question(user_id=current_user.id, question_id=question_id)
    return {"message": "Bookmark removed"}
