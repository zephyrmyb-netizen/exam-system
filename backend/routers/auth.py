from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import auth as auth_module
from .. import crud, schemas
from ..config import INVITE_CODE
from ..database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: schemas.UserCreate, db: Session = Depends(get_db)):
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
def login(body: schemas.LoginRequest, db: Session = Depends(get_db)):
    try:
        user = crud.get_user_by_username(db, body.username)
        if not user or not auth_module.verify_password(body.password, user.password_hash):
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        token = auth_module.create_access_token(data={"sub": str(user.id)})
        return schemas.TokenResponse(access_token=token, token=token)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="登录失败，请稍后重试") from exc


@router.get("/me", response_model=schemas.UserOut)
def me(current_user=Depends(auth_module.get_current_user)):
    return current_user
