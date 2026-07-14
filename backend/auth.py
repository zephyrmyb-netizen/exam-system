from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session, joinedload

from . import models
from .config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from .database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ACCESS_TOKEN_COOKIE = "xuexibao_access"
security = HTTPBearer(auto_error=False)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def _resolve_access_token(request: Request, credentials: HTTPAuthorizationCredentials | None) -> str:
    if credentials and credentials.credentials:
        return credentials.credentials
    return request.cookies.get(ACCESS_TOKEN_COOKIE, "")


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> models.User:
    token = _resolve_access_token(request, credentials)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效或过期的 token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except JWTError:
        raise credentials_exception

    user = (
        db.query(models.User)
        .options(joinedload(models.User.role_ref))
        .filter(models.User.id == user_id)
        .first()
    )
    if user is None:
        raise credentials_exception
    return user


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db),
) -> models.User | None:
    """Return the current user if a valid Bearer token is present, else None.

    This makes authentication optional — endpoints can use this to
    optionally identify the user without requiring login.
    """
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.removeprefix("Bearer ").strip() if auth_header.startswith("Bearer ") else ""
    if not token:
        token = request.cookies.get(ACCESS_TOKEN_COOKIE, "")
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            return None
        user = (
            db.query(models.User)
            .options(joinedload(models.User.role_ref))
            .filter(models.User.id == int(user_id_str))
            .first()
        )
        return user
    except JWTError:
        return None
