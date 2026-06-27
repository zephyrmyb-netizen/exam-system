"""Authentication service helpers for the Phase 2 service layer."""

from sqlalchemy.orm import Session

from .. import auth, crud, models, schemas


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_username(self, username: str) -> models.User | None:
        return crud.get_user_by_username(self.db, username)

    def create_user(self, user_in: schemas.UserCreate) -> models.User:
        password_hash = auth.get_password_hash(user_in.password)
        return crud.create_user(self.db, user_in, password_hash)

    def verify_password(self, plain_password: str, password_hash: str) -> bool:
        return auth.verify_password(plain_password, password_hash)
