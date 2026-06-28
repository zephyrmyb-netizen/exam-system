from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend import models
from backend.api.exams import router as exams_router
from backend.auth import get_current_user
from backend.database import get_db


def _make_app(db_session, current_user=None) -> FastAPI:
    app = FastAPI()
    app.include_router(exams_router)

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    if current_user is not None:
        app.dependency_overrides[get_current_user] = lambda: current_user
    return app


def _make_user(db_session, username="exam_api_user", role_name=None):
    role_id = None
    if role_name:
        role = models.Role(name=role_name)
        db_session.add(role)
        db_session.commit()
        db_session.refresh(role)
        role_id = role.id
    user = models.User(username=username, password_hash="x", role_id=role_id)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _make_course(db_session, owner_id):
    course = models.QuestionBank(owner_id=owner_id, name="Exam API Course", created_at=datetime.now(UTC))
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)
    return course


def _make_question(db_session, owner_id, course_id):
    question = models.Question(
        owner_id=owner_id,
        course_id=course_id,
        type="single_choice",
        question="1+1=?",
        options='{"A":"1","B":"2"}',
        answer="B",
        created_at=datetime.now(UTC),
    )
    db_session.add(question)
    db_session.commit()
    db_session.refresh(question)
    return question


def test_exam_api_create_publish_take_submit_flow(db_session):
    user = _make_user(db_session, role_name="teacher")
    course = _make_course(db_session, user.id)
    question = _make_question(db_session, user.id, course.id)
    client = TestClient(_make_app(db_session, user))

    create_resp = client.post(
        "/exams/",
        json={"title": "API Exam", "course_id": course.id, "question_ids": [question.id], "total_score": 10},
    )
    assert create_resp.status_code == 201
    exam_id = create_resp.json()["id"]

    publish_resp = client.post(f"/exams/{exam_id}/publish")
    assert publish_resp.status_code == 200
    assert publish_resp.json()["status"] == "published"

    start_resp = client.post(f"/exams/{exam_id}/start")
    assert start_resp.status_code == 200
    assert start_resp.json()["exam_id"] == exam_id

    submit_resp = client.post(f"/exams/{exam_id}/submit", json={"answers": {str(question.id): "B"}})
    assert submit_resp.status_code == 200
    assert submit_resp.json()["score"] == 10
    assert submit_resp.json()["correct_count"] == 1


def test_exam_api_lists_only_published_exams(db_session):
    user = _make_user(db_session, role_name="teacher")
    course = _make_course(db_session, user.id)
    client = TestClient(_make_app(db_session, user))

    draft_id = client.post("/exams/", json={"title": "Draft", "course_id": course.id}).json()["id"]
    published_id = client.post("/exams/", json={"title": "Published", "course_id": course.id}).json()["id"]
    client.post(f"/exams/{published_id}/publish")

    response = client.get("/exams/")

    assert response.status_code == 200
    ids = {item["id"] for item in response.json()["items"]}
    assert published_id in ids
    assert draft_id not in ids
