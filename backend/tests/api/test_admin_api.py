from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend import models
from backend.api.admin import router as admin_router
from backend.auth import get_current_user
from backend.database import get_db


def _make_app(db_session, current_user=None) -> FastAPI:
    app = FastAPI()
    app.include_router(admin_router)

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    if current_user is not None:
        app.dependency_overrides[get_current_user] = lambda: current_user
    return app


def _make_user(db_session, username, role_name=None):
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


def test_admin_lists_users(db_session):
    admin = _make_user(db_session, "admin_user", "admin")
    student = _make_user(db_session, "student_user")
    client = TestClient(_make_app(db_session, admin))

    response = client.get("/admin/users")

    assert response.status_code == 200
    names = {item["username"] for item in response.json()["items"]}
    assert "admin_user" in names
    assert student.username in names


def test_admin_updates_user_role(db_session):
    admin = _make_user(db_session, "admin_role_user", "admin")
    target = _make_user(db_session, "target_user")
    client = TestClient(_make_app(db_session, admin))

    response = client.patch(f"/admin/users/{target.id}/role", json={"role": "teacher"})

    assert response.status_code == 200
    assert response.json()["role"] == "teacher"


def test_student_cannot_access_admin_users(db_session):
    student = _make_user(db_session, "not_admin")
    client = TestClient(_make_app(db_session, student))

    response = client.get("/admin/users")

    assert response.status_code == 403


def test_admin_stats_returns_global_counts(db_session):
    admin = _make_user(db_session, "stats_admin", "admin")
    course = models.QuestionBank(owner_id=admin.id, name="Stats bank", created_at=datetime.now(UTC))
    db_session.add(course)
    db_session.commit()
    question = models.Question(
        owner_id=admin.id,
        course_id=course.id,
        type="true_false",
        question="Sky is blue",
        answer="True",
        created_at=datetime.now(UTC),
    )
    db_session.add(question)
    db_session.commit()
    client = TestClient(_make_app(db_session, admin))

    response = client.get("/admin/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["user_count"] >= 1
    assert data["course_count"] == 1
    assert data["question_count"] == 1
