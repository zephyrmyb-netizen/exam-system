from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import select as sa_select

from . import models, schemas
from .crud_common import _add_bank_visibility_filter, apply_pagination


def create_question_bank(
    db: Session, bank_in: schemas.CourseCreate, owner_id: int
) -> models.QuestionBank:
    bank = models.QuestionBank(
        owner_id=owner_id,
        name=bank_in.name,
        description=bank_in.description,
        subject=bank_in.subject,
        visibility=bank_in.visibility,
        created_at=datetime.now(timezone.utc),
    )
    db.add(bank)
    db.commit()
    db.refresh(bank)
    return bank


def get_or_create_uncategorized_bank(db: Session, user_id: int) -> models.QuestionBank:
    """Find the user's 'Uncategorized' bank or create one."""
    bank = (
        db.query(models.QuestionBank)
        .filter(models.QuestionBank.owner_id == user_id, models.QuestionBank.name == "未分类题库")
        .first()
    )
    if bank:
        return bank
    bank = models.QuestionBank(
        owner_id=user_id,
        name="未分类题库",
        description="自动创建的默认题库",
        visibility="private",
        created_at=datetime.now(timezone.utc),
    )
    db.add(bank)
    db.commit()
    db.refresh(bank)
    return bank


def resolve_course(
    db: Session,
    user_id: int,
    course_id: int | None = None,
    course_name: str | None = None,
) -> tuple[models.QuestionBank, bool]:
    """Resolve course_id to bank, or course_name to find-or-create, or fallback."""
    if course_id is not None:
        bank = db.query(models.QuestionBank).filter(models.QuestionBank.id == course_id).first()
        if not bank:
            raise ValueError(f"课程（题库）不存在: course_id={course_id}")
        if bank.owner_id != user_id:
            raise ValueError("无权使用此课程（题库）")
        return bank, False

    name = (course_name or "").strip()
    if name:
        bank = (
            db.query(models.QuestionBank)
            .filter(models.QuestionBank.owner_id == user_id, models.QuestionBank.name == name)
            .first()
        )
        if bank:
            return bank, False
        bank = models.QuestionBank(
            owner_id=user_id,
            name=name,
            description=f"从文件导入: {name}",
            visibility="private",
            created_at=datetime.now(timezone.utc),
        )
        db.add(bank)
        db.commit()
        db.refresh(bank)
        return bank, True

    bank = get_or_create_uncategorized_bank(db, user_id)
    return bank, True


def get_question_banks(
    db: Session, user_id: int | None, page: int = 0, page_size: int = 0,
) -> tuple[list[models.QuestionBank], int]:
    query = _add_bank_visibility_filter(db.query(models.QuestionBank), user_id)
    query = query.order_by(models.QuestionBank.created_at.desc())
    return apply_pagination(query, page, page_size)


def get_my_question_banks(
    db: Session, user_id: int, page: int = 0, page_size: int = 0,
) -> tuple[list[models.QuestionBank], int]:
    from sqlalchemy.orm import selectinload

    query = (
        db.query(models.QuestionBank)
        .filter(models.QuestionBank.owner_id == user_id)
        .options(selectinload(models.QuestionBank.questions))
        .order_by(models.QuestionBank.created_at.desc())
    )
    return apply_pagination(query, page, page_size)


def get_public_question_banks(
    db: Session,
    page: int = 0,
    page_size: int = 0,
    keyword: str = "",
    subject: str = "",
) -> tuple[list[models.QuestionBank], int]:
    from sqlalchemy import or_

    query = db.query(models.QuestionBank).filter(models.QuestionBank.visibility == "public")

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(
                models.QuestionBank.name.like(like),
                models.QuestionBank.description.like(like),
                models.QuestionBank.subject.like(like),
            )
        )
    if subject:
        query = query.filter(models.QuestionBank.subject == subject)

    query = query.order_by(models.QuestionBank.created_at.desc())
    return apply_pagination(query, page, page_size)


def get_question_bank_by_id(db: Session, bank_id: int) -> Optional[models.QuestionBank]:
    return db.query(models.QuestionBank).filter(models.QuestionBank.id == bank_id).first()


def delete_question_bank(db: Session, bank_id: int) -> bool:
    bank = db.query(models.QuestionBank).filter(models.QuestionBank.id == bank_id).first()
    if not bank:
        return False

    # Use subquery (wrapped in select() to avoid SA coercion warnings).
    qid_subq = (
        db.query(models.Question.id)
        .filter(models.Question.course_id == bank_id)
        .subquery()
    )
    qid_sel = sa_select(qid_subq)

    db.query(models.PracticeRecord).filter(
        models.PracticeRecord.question_id.in_(qid_sel)
    ).update({"question_id": None}, synchronize_session=False)
    db.query(models.PracticeRecord).filter(
        models.PracticeRecord.course_id == bank_id
    ).update({"course_id": None}, synchronize_session=False)

    db.query(models.UserQuestionReview).filter(
        models.UserQuestionReview.question_id.in_(qid_sel)
    ).update({"question_id": None}, synchronize_session=False)
    db.query(models.UserQuestionReview).filter(
        models.UserQuestionReview.course_id == bank_id
    ).update({"course_id": None}, synchronize_session=False)

    db.delete(bank)
    db.commit()
    return True


def update_question_bank_visibility(
    db: Session, bank_id: int, visibility: str
) -> Optional[models.QuestionBank]:
    bank = db.query(models.QuestionBank).filter(models.QuestionBank.id == bank_id).first()
    if not bank:
        return None
    bank.visibility = visibility
    db.commit()
    db.refresh(bank)
    return bank


def update_question_bank(
    db: Session, bank_id: int, data: schemas.CourseUpdate,
) -> Optional[models.QuestionBank]:
    bank = db.query(models.QuestionBank).filter(models.QuestionBank.id == bank_id).first()
    if not bank:
        return None
    if data.name is not None:
        if not data.name.strip():
            raise ValueError("课程名称不能为空")
        bank.name = data.name.strip()
    if data.description is not None:
        bank.description = data.description
    if data.subject is not None:
        bank.subject = data.subject
    db.commit()
    db.refresh(bank)
    return bank
