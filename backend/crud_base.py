from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from sqlalchemy.orm import Session

from .crud_common import MAX_UNPAGINATED_ROWS

ModelType = TypeVar("ModelType")
CreateSchema = TypeVar("CreateSchema")
UpdateSchema = TypeVar("UpdateSchema")


@dataclass
class PaginatedResult:
    """Generic paginated query result."""

    items: list[Any]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        if self.page_size <= 0:
            return 0 if self.total == 0 else 1
        return math.ceil(self.total / self.page_size)

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        return self.page > 1


class GenericCRUD(Generic[ModelType, CreateSchema, UpdateSchema]):
    """Small reusable CRUD base for repository-style helpers."""

    def __init__(
        self,
        model: type[ModelType],
        create_schema: type[CreateSchema] | None = None,
        update_schema: type[UpdateSchema] | None = None,
    ):
        self.model = model
        self.create_schema = create_schema
        self.update_schema = update_schema

    def get_by_id(self, db: Session, id: int) -> ModelType | None:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_list(self, db: Session, *, skip: int = 0, limit: int = 0) -> list[ModelType]:
        query = db.query(self.model)
        if skip:
            query = query.offset(skip)
        if limit:
            query = query.limit(limit)
        return query.all()

    def paginate(self, db: Session, *, page: int = 0, page_size: int = 0) -> PaginatedResult:
        query = db.query(self.model)
        total = query.count()
        if page > 0 and page_size > 0:
            query = query.offset((page - 1) * page_size).limit(page_size)
        else:
            query = query.limit(MAX_UNPAGINATED_ROWS)
        return PaginatedResult(items=query.all(), total=total, page=page, page_size=page_size)

    def delete(self, db: Session, id: int) -> bool:
        obj = self.get_by_id(db, id)
        if obj is None:
            return False
        db.delete(obj)
        db.commit()
        return True
