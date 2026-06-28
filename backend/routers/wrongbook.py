from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import auth as auth_module
from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/wrongbook", tags=["wrongbook"])


@router.get("/")
def list_wrong_records(
    page: int = Query(0, ge=0, description="页码（0表示不分页）"),
    page_size: int = Query(0, ge=0, description="每页数量（0表示不分页）"),
    keyword: str = Query("", description="关键词搜索"),
    subject: str = Query("", description="科目筛选"),
    chapter: str = Query("", description="章节筛选"),
    type: str = Query("", alias="type", description="题目类型筛选"),
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    records, total = crud.get_wrong_records(
        db,
        current_user.id,
        page=page,
        page_size=page_size,
        keyword=keyword,
        subject=subject,
        chapter=chapter,
        q_type=type,
    )
    result = [schemas.WrongRecordOut.model_validate(r).model_dump() for r in records]

    # Legacy mode: no pagination params → return flat array
    if page <= 0 or page_size <= 0:
        return result

    return {"total": total, "page": page, "page_size": page_size, "items": result}


@router.delete("/{question_id}")
def remove_wrong_record(
    question_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    deleted = crud.delete_wrong_record(db, current_user.id, question_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="错题记录不存在")
    return {"message": "已从错题本移除"}


@router.get("/meta")
def wrongbook_meta(
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    """Get distinct subjects and chapters from questions in user wrong records."""
    return crud.get_wrongbook_meta(db, current_user.id)
