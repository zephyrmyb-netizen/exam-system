"""Question repository placeholder for Phase 2 layering."""

from .. import models
from .base import BaseRepository


class QuestionRepository(BaseRepository[models.Question]):
    model = models.Question
