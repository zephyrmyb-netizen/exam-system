"""Tests for the new layered courses API router.

The router is mounted on a standalone FastAPI app so it can be validated
without clashing with the legacy /courses router that remains mounted in main.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend import models
from backend.api.courses import router as courses_router
from backend.auth import get_current_user
from backend.database import get_db


def _make_app(db_session, current_user=None) -> FastAPI:
    app = FastAPI()
    app.include_router(courses_router)

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    if current_user is not None:
        app.dependency_overrides[get_current_user] = lambda: current_user
    return app


def _make_user(db_session, username: str) -> models.User:
    user = models.User(username=username, password_hash="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _make_bank(
    db_session,
    owner_id: int,
    name: str,
    visibility: str = "private",
) -> models.QuestionBank:
    bank = models.QuestionBank(
        owner_id=owner_id,
        name=name,
        description="",
        subject="",
        visibility=visibility,
    )
    db_session.add(bank)
    db_session.commit()
    db_session.refresh(bank)
    return bank


def test_list_courses_requires_auth(db_session):
    client = TestClient(_make_app(db_session))

    response = client.get("/courses/")

    assert response.status_code in (401, 403)


def test_layered_list_courses_returns_visible_courses(db_session):
    owner = _make_user(db_session, "api_course_owner")
    viewer = _make_user(db_session, "api_course_viewer")
    public_bank = _make_bank(db_session, owner.id, "Public bank", "public")
    _make_bank(db_session, owner.id, "Hidden bank", "private")
    owned_bank = _make_bank(db_session, viewer.id, "Owned bank", "private")

    client = TestClient(_make_app(db_session, viewer))

    response = client.get("/courses/?page=1&page_size=20")

    assert response.status_code == 200
    data = response.json()
    names = {item["name"] for item in data["items"]}
    assert data["total"] == 2
    assert public_bank.name in names
    assert owned_bank.name in names
    assert "Hidden bank" not in names


def test_layered_list_my_courses_returns_only_owned_courses(db_session):
    owner = _make_user(db_session, "api_my_owner")
    other = _make_user(db_session, "api_my_other")
    owned_bank = _make_bank(db_session, owner.id, "My bank", "private")
    _make_bank(db_session, other.id, "Other bank", "public")

    client = TestClient(_make_app(db_session, owner))

    response = client.get("/courses/mine?page=1&page_size=20")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == owned_bank.id


def test_layered_get_course_404_when_missing(db_session):
    user = _make_user(db_session, "api_missing_course_user")
    client = TestClient(_make_app(db_session, user))

    response = client.get("/courses/999999")

    assert response.status_code == 404


def test_layered_get_course_hides_private_course_from_other_user(db_session):
    owner = _make_user(db_session, "api_private_owner")
    viewer = _make_user(db_session, "api_private_viewer")
    bank = _make_bank(db_session, owner.id, "Private bank", "private")
    client = TestClient(_make_app(db_session, viewer))

    response = client.get(f"/courses/{bank.id}")

    assert response.status_code == 404
