import json
from datetime import UTC, datetime

from backend import crud, models
from backend.services.practice_service import PracticeService


def _make_user(db_session, username: str) -> models.User:
    user = models.User(username=username, password_hash="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _make_bank(db_session, owner_id: int) -> models.QuestionBank:
    bank = models.QuestionBank(
        owner_id=owner_id,
        name="Practice service bank",
        visibility="private",
        created_at=datetime.now(UTC),
    )
    db_session.add(bank)
    db_session.commit()
    db_session.refresh(bank)
    return bank


def _make_question(db_session, owner_id: int, course_id: int) -> models.Question:
    question = models.Question(
        owner_id=owner_id,
        course_id=course_id,
        visibility="private",
        source="manual",
        subject="Java",
        chapter="基础",
        type="single_choice",
        question="Java 的入口方法是什么？",
        options=json.dumps({"A": "main", "B": "start"}, ensure_ascii=False),
        answer="A",
        analysis="main 方法是入口。",
        difficulty="normal",
    )
    db_session.add(question)
    db_session.commit()
    db_session.refresh(question)
    return question


def test_practice_service_returns_user_stats(db_session):
    user = _make_user(db_session, "practice_service_user")
    bank = _make_bank(db_session, user.id)
    question = _make_question(db_session, user.id, bank.id)
    crud.create_practice_record(
        db_session,
        user_id=user.id,
        question_id=question.id,
        course_id=bank.id,
        question_type=question.type,
        is_correct=True,
        user_answer="A",
        correct_answer="A",
    )
    db_session.commit()

    stats = PracticeService(db_session).get_stats(user_id=user.id)

    assert stats["total_count"] == 1
    assert stats["correct_count"] == 1


def test_practice_service_returns_history(db_session):
    user = _make_user(db_session, "practice_service_history")
    bank = _make_bank(db_session, user.id)
    question = _make_question(db_session, user.id, bank.id)
    crud.create_practice_record(
        db_session,
        user_id=user.id,
        question_id=question.id,
        course_id=bank.id,
        question_type=question.type,
        is_correct=False,
        user_answer="B",
        correct_answer="A",
    )
    db_session.commit()

    records, total = PracticeService(db_session).get_history(user_id=user.id)

    assert total == 1
    assert records[0].user_answer == "B"
