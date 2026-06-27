"""User repository."""

from .. import models
from .base import BaseRepository


class UserRepository(BaseRepository[models.User]):
    model = models.User

    def get_by_username(self, username: str) -> models.User | None:
        return self.query().filter(models.User.username == username).first()
