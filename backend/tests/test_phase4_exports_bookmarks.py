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


def test_bookmarks_api_requires_login(client):
    response = client.get("/bookmarks/")

    assert response.status_code == 401


def test_bookmarks_api_adds_lists_and_removes_bookmark(client, auth_headers):
    course_resp = client.post("/courses/", headers=auth_headers, json={"name": "Java"})
    question_resp = client.post(
        "/questions/",
        headers=auth_headers,
        json={
            "course_id": course_resp.json()["id"],
            "type": "single_choice",
            "question": "What is JVM?",
            "options": {"A": "Java Virtual Machine", "B": "JavaScript"},
            "answer": "A",
        },
    )
    question_id = question_resp.json()["id"]

    add_resp = client.post(
        "/bookmarks/",
        headers=auth_headers,
        json={"question_id": question_id, "folder_name": "重点", "note": "复习 JVM"},
    )
    assert add_resp.status_code == 201
    assert add_resp.json()["question_id"] == question_id

    list_resp = client.get("/bookmarks/", headers=auth_headers)
    assert list_resp.status_code == 200
    payload = list_resp.json()
    assert payload["total"] == 1
    assert payload["items"][0]["question"]["question"] == "What is JVM?"
    assert payload["folders"] == ["重点"]

    delete_resp = client.delete(f"/bookmarks/{question_id}", headers=auth_headers)
    assert delete_resp.status_code == 200
    assert client.get("/bookmarks/", headers=auth_headers).json()["total"] == 0


def test_bookmark_add_is_idempotent_and_updates_folder(client, auth_headers):
    course_id = client.post("/courses/", headers=auth_headers, json={"name": "Java"}).json()["id"]
    client.post(
        "/questions/",
        headers=auth_headers,
        json={
            "course_id": course_id,
            "type": "fill_blank",
            "question": "Java bytecode runs on ___.",
            "answer": "JVM",
        },
    )
    question_id = client.get("/questions/", headers=auth_headers).json()[0]["id"]

    first = client.post("/bookmarks/", headers=auth_headers, json={"question_id": question_id, "folder_name": "A"})
    second = client.post("/bookmarks/", headers=auth_headers, json={"question_id": question_id, "folder_name": "B"})

    assert first.status_code == 201
    assert second.status_code == 201
    payload = client.get("/bookmarks/", headers=auth_headers).json()
    assert payload["total"] == 1
    assert payload["items"][0]["folder_name"] == "B"


def test_bookmarks_are_user_scoped(client, auth_headers, auth_headers_other):
    course_id = client.post("/courses/", headers=auth_headers, json={"name": "Java"}).json()["id"]
    create_resp = client.post(
        "/questions/",
        headers=auth_headers,
        json={
            "course_id": course_id,
            "type": "short_answer",
            "question": "Explain JVM",
            "answer": "Java Virtual Machine",
        },
    )
    question_id = create_resp.json()["id"]
    client.post("/bookmarks/", headers=auth_headers, json={"question_id": question_id})

    assert client.get("/bookmarks/", headers=auth_headers).json()["total"] == 1
    assert client.get("/bookmarks/", headers=auth_headers_other).json()["total"] == 0
