"""Repository helpers for course collaboration records."""

from __future__ import annotations

from .. import models
from .base import BaseRepository


class CollaborationRepository(BaseRepository[models.Collaboration]):
    """Data access for question-bank collaborators."""

    model = models.Collaboration

    def get_for_course(self, course_id: int) -> list[models.Collaboration]:
        return (
            self.query()
            .filter(models.Collaboration.course_id == course_id)
            .order_by(models.Collaboration.created_at.desc(), models.Collaboration.id.desc())
            .all()
        )

    def get_for_user(self, user_id: int) -> list[models.Collaboration]:
        return (
            self.query()
            .filter(models.Collaboration.user_id == user_id)
            .order_by(models.Collaboration.created_at.desc(), models.Collaboration.id.desc())
            .all()
        )

    def find(self, course_id: int, user_id: int) -> models.Collaboration | None:
        return (
            self.query()
            .filter(
                models.Collaboration.course_id == course_id,
                models.Collaboration.user_id == user_id,
            )
            .first()
        )

    def add_collaborator(
        self,
        *,
        course_id: int,
        user_id: int,
        role: str = "viewer",
        invited_by: int | None = None,
    ) -> models.Collaboration:
        collaboration = models.Collaboration(
            course_id=course_id,
            user_id=user_id,
            role=role,
            invited_by=invited_by,
        )
        self.db.add(collaboration)
        self.db.commit()
        self.db.refresh(collaboration)
        return collaboration
