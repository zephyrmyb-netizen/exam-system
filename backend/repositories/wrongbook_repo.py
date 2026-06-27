"""Wrongbook repository placeholder for Phase 2 layering."""

from .. import models
from .base import BaseRepository


class WrongbookRepository(BaseRepository[models.WrongRecord]):
    model = models.WrongRecord
