"""Practice business service.

This service is intentionally thin at Phase 2. Existing routers still own the
public contract, while this layer gives later refactors a tested place to move
practice rules.
"""

from sqlalchemy.orm import Session

from .. import models
from ..repositories.practice_repo import PracticeRepository


class PracticeService:
    def __init__(self, db: Session, repo: PracticeRepository | None = None):
        self.db = db
        self.repo = repo or PracticeRepository(db)

    def get_stats(self, *, user_id: int) -> dict:
        return self.repo.get_stats(user_id=user_id)

    def get_history(
        self,
        *,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[models.PracticeRecord], int]:
        return self.repo.get_history(user_id=user_id, page=page, page_size=page_size)
