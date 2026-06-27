"""Practice repository."""

from .. import crud, models
from .base import BaseRepository


class PracticeRepository(BaseRepository[models.PracticeRecord]):
    model = models.PracticeRecord

    def get_stats(self, *, user_id: int) -> dict:
        return crud.get_practice_stats(self.db, user_id=user_id)

    def get_history(
        self,
        *,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[models.PracticeRecord], int]:
        return crud.get_practice_history(self.db, user_id=user_id, page=page, page_size=page_size)
