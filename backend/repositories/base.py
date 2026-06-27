"""Base repository helpers for SQLAlchemy-backed data access."""

from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy.orm import Query, Session

from ..crud_common import apply_pagination

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """Small repository base.

    Business rules stay in services; repositories only compose queries.
    """

    model: type[ModelType]

    def __init__(self, db: Session):
        self.db = db

    def query(self) -> Query:
        return self.db.query(self.model)

    def get_by_id(self, id: int) -> ModelType | None:
        return self.query().filter(self.model.id == id).first()

    def list_all(self, *, page: int = 0, page_size: int = 0) -> tuple[list[ModelType], int]:
        return apply_pagination(self.query(), page, page_size)
