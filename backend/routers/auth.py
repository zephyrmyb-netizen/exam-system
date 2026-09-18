import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from .. import auth as auth_module
from .. import crud, schemas
from ..config import ACCESS_TOKEN_EXPIRE_MINUTES, APP_ENV, AUTH_RATE_LIMIT_PER_MINUTE, INVITE_CODE, IS_PRODUCTION
from ..database import get_db
from ..models import User
from ..ratelimit import RateLimiter, get_limiter

router = APIRouter(prefix="/auth", tags=["auth"])


def rate_limiter() -> RateLimiter:
    """FastAPI dependency returning the active rate limiter.

    Override in tests via ``app.dependency_overrides[rate_limiter]``.
    """
    return get_limiter()


def _client_ip(request: Request) -> str:
    """Best-effort client IP for pre-auth rate limiting.

    Order: CF-Connecting-IP (set by the Cloudflare tunnel edge), then the
    leftmost X-Forwarded-For entry (nginx / beta gateway), then the socket
    address for direct access.
    """
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def enforce_auth_limit(request: Request, limiter: RateLimiter = Depends(rate_limiter)) -> None:
    """Per-IP limit on unauthenticated auth attempts (anti credential-stuffing).

    Applies to login/register/guest before any credential or DB work, and is
    shared with the nginx edge limit so both deployment paths are covered.
    """
    limiter.check(
        key=f"auth:ip:{_client_ip(request)}",
        limit=AUTH_RATE_LIMIT_PER_MINUTE,
        window_s=60,
        message=f"尝试过于频繁，每分钟最多 {AUTH_RATE_LIMIT_PER_MINUTE} 次，请稍后再试。",
    )


def _set_access_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=auth_module.ACCESS_TOKEN_COOKIE,
        value=token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax",
        path="/",
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: schemas.UserCreate, db: Session = Depends(get_db), _ratelimit=Depends(enforce_auth_limit)):
    try:
        invite_code = body.invite_code
        if not invite_code:
            raise HTTPException(status_code=400, detail="邀请码不能为空")
        if invite_code != INVITE_CODE:
            raise HTTPException(status_code=400, detail="邀请码错误")

        if not body.username.strip() or not body.password:
            raise HTTPException(status_code=400, detail="用户名和密码不能为空")

        existing = crud.get_user_by_username(db, body.username)
        if existing:
            raise HTTPException(status_code=400, detail="用户名已存在")

        password_hash = auth_module.get_password_hash(body.password)
        crud.create_user(db, body, password_hash)
        return {"message": "注册成功"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="注册失败，请稍后重试") from exc


@router.post("/login", response_model=schemas.TokenResponse)
def login(body: schemas.LoginRequest, response: Response, db: Session = Depends(get_db), _ratelimit=Depends(enforce_auth_limit)):
    try:
        user = crud.get_user_by_username(db, body.username)
        if not user or not auth_module.verify_password(body.password, user.password_hash):
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        token = auth_module.create_access_token(data={"sub": str(user.id)})
        _set_access_cookie(response, token)
        return schemas.TokenResponse(access_token=token, token=token)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="登录失败，请稍后重试") from exc


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    response.delete_cookie(key=auth_module.ACCESS_TOKEN_COOKIE, path="/", secure=IS_PRODUCTION, samesite="lax")


@router.post("/guest", response_model=schemas.TokenResponse, status_code=status.HTTP_201_CREATED)
def guest_login(
    body: schemas.GuestLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
    _ratelimit=Depends(enforce_auth_limit),
):
    """Create an isolated disposable user for the local beta environment only."""
    if APP_ENV != "testing":
        raise HTTPException(status_code=404, detail="Not found")

    nickname = body.nickname.strip() or f"游客{secrets.randbelow(9000) + 1000}"

    username = f"guest_{secrets.token_urlsafe(12).replace('-', '').replace('_', '')[:16]}"
    guest = User(
        username=username,
        password_hash=auth_module.get_password_hash(secrets.token_urlsafe(32)),
        display_name=nickname,
        is_guest=1,
    )
    db.add(guest)
    db.commit()
    db.refresh(guest)

    token = auth_module.create_access_token(data={"sub": str(guest.id)})
    _set_access_cookie(response, token)
    return schemas.TokenResponse(access_token=token, token=token)


@router.delete("/guest/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_guest_account(response: Response, current_user=Depends(auth_module.get_current_user), db: Session = Depends(get_db)):
    """Delete only the current disposable guest and its cascaded beta data."""
    if APP_ENV != "testing" or not bool(current_user.is_guest):
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(current_user)
    db.commit()
    response.delete_cookie(key=auth_module.ACCESS_TOKEN_COOKIE, path="/", secure=IS_PRODUCTION, samesite="lax")


@router.get("/me", response_model=schemas.UserOut)
def me(current_user=Depends(auth_module.get_current_user)):
    return current_user
