"""Phase 4 M3 coverage for exports and bookmarks."""

import csv
import io
import json

from backend import models
from backend.services.export_service import ExportService


def _user(db_session, username="alice"):
    user = models.User(username=username, password_hash="hash")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _course(db_session, owner_id, name="Java Review"):
    course = models.QuestionBank(owner_id=owner_id, name=name, visibility="private", subject="Java")
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)
    return course


def _question(db_session, owner_id, course_id, text="What is JVM?"):
    question = models.Question(
        owner_id=owner_id,
        course_id=course_id,
        type="single_choice",
        question=text,
        options='{"A":"Java Virtual Machine","B":"JavaScript"}',
        answer="A",
        analysis="JVM runs Java bytecode.",
        subject="Java",
        chapter="Basics",
        difficulty="normal",
    )
    db_session.add(question)
    db_session.commit()
    db_session.refresh(question)
    return question


def test_export_course_json_contains_course_and_questions(db_session):
    user = _user(db_session)
    course = _course(db_session, user.id)
    _question(db_session, user.id, course.id)

    payload = json.loads(ExportService(db_session).export_course_json(course.id))

    assert payload["name"] == "Java Review"
    assert payload["subject"] == "Java"
    assert payload["questions"][0]["question"] == "What is JVM?"
    assert payload["questions"][0]["options"]["A"] == "Java Virtual Machine"


def test_export_course_excel_returns_xlsx_bytes(db_session):
    user = _user(db_session)
    course = _course(db_session, user.id)
    _question(db_session, user.id, course.id)

    payload = ExportService(db_session).export_course_excel(course.id)

    assert payload[:2] == b"PK"


def test_export_practice_history_csv_is_user_scoped(db_session):
    user = _user(db_session)
    other = _user(db_session, "other")
    course = _course(db_session, user.id)
    question = _question(db_session, user.id, course.id)
    db_session.add_all(
        [
            models.PracticeRecord(
                user_id=user.id,
                question_id=question.id,
                course_id=course.id,
                question_type=question.type,
                is_correct=1,
                user_answer="A",
                correct_answer="A",
            ),
            models.PracticeRecord(
                user_id=other.id,
                question_id=question.id,
                course_id=course.id,
                question_type=question.type,
                is_correct=0,
                user_answer="B",
                correct_answer="A",
            ),
        ]
    )
    db_session.commit()

    reader = csv.DictReader(io.StringIO(ExportService(db_session).export_practice_history_csv(user_id=user.id)))
    rows = list(reader)

    assert len(rows) == 1
    assert rows[0]["user_answer"] == "A"
    assert rows[0]["is_correct"] == "true"


def test_export_api_requires_login(client):
    response = client.get("/exports/practice-history.csv")

    assert response.status_code == 401


def test_export_api_downloads_practice_history(client, auth_headers):
    response = client.get("/exports/practice-history.csv", headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
