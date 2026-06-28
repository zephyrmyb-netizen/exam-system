"""Bookmark repository helpers."""

from sqlalchemy.orm import joinedload

from .. import models
from .base import BaseRepository


class BookmarkRepository(BaseRepository[models.Bookmark]):
    model = models.Bookmark

    def get_for_user_question(self, *, user_id: int, question_id: int) -> models.Bookmark | None:
        return (
            self.query()
            .options(joinedload(models.Bookmark.question))
            .filter(models.Bookmark.user_id == user_id, models.Bookmark.question_id == question_id)
            .first()
        )

    def list_for_user(self, *, user_id: int, folder: str = "") -> tuple[list[models.Bookmark], int]:
        query = (
            self.query()
            .options(joinedload(models.Bookmark.question))
            .filter(models.Bookmark.user_id == user_id)
            .order_by(models.Bookmark.created_at.desc(), models.Bookmark.id.desc())
        )
        if folder:
            query = query.filter(models.Bookmark.folder_name == folder)
        items = query.all()
        return items, len(items)

    def list_folders_for_user(self, *, user_id: int) -> list[str]:
        rows = (
            self.db.query(models.Bookmark.folder_name)
            .filter(models.Bookmark.user_id == user_id)
            .order_by(models.Bookmark.folder_name.asc())
            .distinct()
            .all()
        )
        return [row[0] for row in rows if row[0]]

    def upsert(
        self,
        *,
        user_id: int,
        question_id: int,
        folder_name: str,
        note: str,
    ) -> models.Bookmark:
        bookmark = self.get_for_user_question(user_id=user_id, question_id=question_id)
        if bookmark is None:
            bookmark = models.Bookmark(
                user_id=user_id,
                question_id=question_id,
                folder_name=folder_name,
                note=note,
            )
            self.db.add(bookmark)
        else:
            bookmark.folder_name = folder_name
            bookmark.note = note
        self.db.commit()
        self.db.refresh(bookmark)
        return bookmark

    def delete_for_user_question(self, *, user_id: int, question_id: int) -> bool:
        bookmark = self.get_for_user_question(user_id=user_id, question_id=question_id)
        if bookmark is None:
            return False
        self.db.delete(bookmark)
        self.db.commit()
        return True
