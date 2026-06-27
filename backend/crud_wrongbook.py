from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models
from .crud_common import _add_question_visibility_filter, apply_pagination


def get_random_wrong_question(
    db: Session, user_id: int, course_id: int | None = None, q_type: str = "",
) -> Optional[models.Question]:
    from random import randint

    wrong_qids = (
        db.query(models.WrongRecord.question_id)
        .filter(models.WrongRecord.user_id == user_id)
    )

    base = _add_question_visibility_filter(
        db.query(models.Question).filter(models.Question.id.in_(wrong_qids)),
        user_id,
    )

    if course_id is not None:
        base = base.filter(models.Question.course_id == course_id)
    if q_type:
        base = base.filter(models.Question.type == q_type)

    # Find the maximum wrong_count among matching questions.
    max_wc = (
        db.query(func.max(models.WrongRecord.wrong_count))
        .filter(models.WrongRecord.user_id == user_id)
        .filter(models.WrongRecord.question_id.in_(
            db.query(models.Question.id).filter(models.Question.id.in_(wrong_qids))
        ))
        .scalar()
    )
    if max_wc is None:
        return None

    # Pick a random question from the highest-wrong-count group.
    top_group = (
        base.join(models.WrongRecord, models.WrongRecord.question_id == models.Question.id)
        .filter(models.WrongRecord.user_id == user_id)
        .filter(models.WrongRecord.wrong_count == max_wc)
        .order_by(models.Question.id)
    )
    count = top_group.count()
    if count == 0:
        return None
    return top_group.offset(randint(0, count - 1)).limit(1).first()


def get_wrong_records(
    db: Session,
    user_id: int,
    page: int = 0,
    page_size: int = 0,
    keyword: str = "",
    subject: str = "",
    chapter: str = "",
    q_type: str = "",
) -> tuple[list[models.WrongRecord], int]:
    query = (
        db.query(models.WrongRecord)
        .filter(models.WrongRecord.user_id == user_id)
        .join(models.Question)
    )

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(models.Question.question.like(like))
    if subject:
        query = query.filter(models.Question.subject == subject)
    if chapter:
        query = query.filter(models.Question.chapter == chapter)
    if q_type:
        query = query.filter(models.Question.type == q_type)

    query = query.order_by(models.WrongRecord.id.desc())
    return apply_pagination(query, page, page_size)


def upsert_wrong_record(db: Session, user_id: int, question_id: int, user_answer: str) -> models.WrongRecord:
    record = (
        db.query(models.WrongRecord)
        .filter(models.WrongRecord.user_id == user_id, models.WrongRecord.question_id == question_id)
        .first()
    )
    if record:
        record.wrong_count += 1
        record.last_wrong_answer = user_answer
    else:
        record = models.WrongRecord(
            user_id=user_id,
            question_id=question_id,
            wrong_count=1,
            last_wrong_answer=user_answer,
        )
        db.add(record)
    db.flush()
    return record


def delete_wrong_record(db: Session, user_id: int, question_id: int) -> bool:
    record = (
        db.query(models.WrongRecord)
        .filter(models.WrongRecord.user_id == user_id, models.WrongRecord.question_id == question_id)
        .first()
    )
    if not record:
        return False
    db.delete(record)
    db.commit()
    return True


def clear_wrong_record_if_correct(db: Session, user_id: int, question_id: int) -> None:
    record = (
        db.query(models.WrongRecord)
        .filter(models.WrongRecord.user_id == user_id, models.WrongRecord.question_id == question_id)
        .first()
    )
    if record:
        db.delete(record)
        db.flush()


def get_wrongbook_meta(db: Session, user_id: int) -> dict:
    subjects = [
        r[0] for r in db.query(models.Question.subject)
        .join(models.WrongRecord)
        .filter(models.WrongRecord.user_id == user_id)
        .distinct().order_by(models.Question.subject).all()
        if r[0]
    ]
    chapters = [
        r[0] for r in db.query(models.Question.chapter)
        .join(models.WrongRecord)
        .filter(models.WrongRecord.user_id == user_id)
        .distinct().order_by(models.Question.chapter).all()
        if r[0]
    ]
    return {"subjects": subjects, "chapters": chapters}
