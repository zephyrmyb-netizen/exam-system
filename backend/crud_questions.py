from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from . import models, schemas
from .crud_common import _add_question_visibility_filter, apply_pagination
from .utils import normalize_answer


def get_questions(
    db: Session,
    user_id: int | None = None,
    page: int = 0,
    page_size: int = 0,
    keyword: str = "",
    subject: str = "",
    chapter: str = "",
    q_type: str = "",
    course_id: int | None = None,
) -> tuple[list[models.Question], int]:
    query = _add_question_visibility_filter(db.query(models.Question), user_id)

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(models.Question.question.like(like))
    if subject:
        query = query.filter(models.Question.subject == subject)
    if chapter:
        query = query.filter(models.Question.chapter == chapter)
    if q_type:
        query = query.filter(models.Question.type == q_type)
    if course_id is not None:
        query = query.filter(models.Question.course_id == course_id)

    query = query.order_by(models.Question.id.desc())
    return apply_pagination(query, page, page_size)


def get_question_by_id(db: Session, question_id: int) -> Optional[models.Question]:
    return db.query(models.Question).filter(models.Question.id == question_id).first()


def get_visible_question_by_id(db: Session, question_id: int, user_id: int) -> Optional[models.Question]:
    query = _add_question_visibility_filter(
        db.query(models.Question).filter(models.Question.id == question_id),
        user_id,
    )
    return query.first()


def create_questions_batch(
    db: Session,
    questions_data: list[schemas.QuestionCreate],
    owner_id: int,
    course_id: int | None = None,
    visibility: str = "private",
    source: str = "import",
) -> int:
    count = 0
    for q in questions_data:
        normalized_answer = normalize_answer(q.answer, q.type)
        q_course_id = course_id if course_id is not None else q.course_id
        question = models.Question(
            owner_id=owner_id,
            course_id=q_course_id,
            visibility=visibility,
            source=source,
            created_at=datetime.now(timezone.utc),
            subject=q.subject,
            chapter=q.chapter,
            type=q.type,
            question=q.question,
            answer=normalized_answer,
            analysis=q.analysis or "",
            difficulty=q.difficulty or "normal",
        )
        question.set_options_dict(q.options)
        db.add(question)
        count += 1
    db.commit()
    return count


def delete_question(db: Session, question_id: int) -> bool:
    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not question:
        return False
    db.delete(question)
    db.commit()
    return True


def create_single_question(
    db: Session, data: schemas.QuestionManualCreate, owner_id: int,
) -> models.Question:
    normalized_answer = normalize_answer(data.answer, data.type)
    question = models.Question(
        owner_id=owner_id,
        course_id=data.course_id,
        visibility="private",
        source="manual",
        created_at=datetime.now(timezone.utc),
        subject=data.subject,
        chapter=data.chapter,
        type=data.type,
        question=data.question,
        answer=normalized_answer,
        analysis=data.analysis or "",
        difficulty=data.difficulty or "normal",
    )
    question.set_options_dict(data.options)
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def update_question(
    db: Session, question_id: int, data: schemas.QuestionUpdate,
) -> Optional[models.Question]:
    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not question:
        return None

    if data.subject is not None:
        question.subject = data.subject
    if data.chapter is not None:
        question.chapter = data.chapter
    if data.type is not None:
        question.type = data.type
    if data.question is not None:
        if not data.question.strip():
            raise ValueError("题目题干不能为空")
        question.question = data.question.strip()
    if data.options is not None:
        question.set_options_dict(data.options)
    if data.answer is not None:
        question.answer = data.answer
    if data.analysis is not None:
        question.analysis = data.analysis
    if data.difficulty is not None:
        question.difficulty = data.difficulty
    if data.course_id is not None:
        question.course_id = data.course_id

    q_type = question.type
    if q_type in ("single_choice", "multiple_choice") and not question.options:
        raise ValueError("选择题（single_choice / multiple_choice）必须提供 options")
    if data.type is not None and data.answer is not None:
        question.answer = normalize_answer(question.answer, question.type)

    db.commit()
    db.refresh(question)
    return question


def update_question_visibility(
    db: Session, question_id: int, visibility: str
) -> Optional[models.Question]:
    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not question:
        return None
    question.visibility = visibility
    db.commit()
    db.refresh(question)
    return question


def get_public_questions(
    db: Session,
    page: int = 0,
    page_size: int = 0,
    keyword: str = "",
    subject: str = "",
    chapter: str = "",
    q_type: str = "",
    course_id: int | None = None,
) -> tuple[list[models.Question], int]:
    query = db.query(models.Question).filter(models.Question.visibility == "public")

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(models.Question.question.like(like))
    if subject:
        query = query.filter(models.Question.subject == subject)
    if chapter:
        query = query.filter(models.Question.chapter == chapter)
    if q_type:
        query = query.filter(models.Question.type == q_type)
    if course_id is not None:
        query = query.filter(models.Question.course_id == course_id)

    query = query.order_by(models.Question.id.desc())
    return apply_pagination(query, page, page_size)


def get_my_questions(
    db: Session,
    user_id: int,
    page: int = 0,
    page_size: int = 0,
    keyword: str = "",
    subject: str = "",
    chapter: str = "",
    q_type: str = "",
    course_id: int | None = None,
) -> tuple[list[models.Question], int]:
    query = db.query(models.Question).filter(models.Question.owner_id == user_id)

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(models.Question.question.like(like))
    if subject:
        query = query.filter(models.Question.subject == subject)
    if chapter:
        query = query.filter(models.Question.chapter == chapter)
    if q_type:
        query = query.filter(models.Question.type == q_type)
    if course_id is not None:
        query = query.filter(models.Question.course_id == course_id)

    query = query.order_by(models.Question.id.desc())
    return apply_pagination(query, page, page_size)


def get_question_meta(db: Session, user_id: int | None = None) -> dict:
    query = _add_question_visibility_filter(
        db.query(models.Question).distinct(), user_id
    )
    subjects = [
        r[0] for r in query.with_entities(models.Question.subject)
        .distinct().order_by(models.Question.subject).all()
        if r[0]
    ]
    chapters = [
        r[0] for r in query.with_entities(models.Question.chapter)
        .distinct().order_by(models.Question.chapter).all()
        if r[0]
    ]
    return {"subjects": subjects, "chapters": chapters}
