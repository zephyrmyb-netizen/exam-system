from datetime import UTC, datetime

import pytest
from fastapi import HTTPException

from backend import models
from backend.services.course_service import CourseService


def _make_user(db_session, username: str) -> models.User:
    user = models.User(username=username, password_hash="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _make_bank(db_session, owner_id: int, name: str, visibility: str = "private"):
    bank = models.QuestionBank(
        owner_id=owner_id,
        name=name,
        visibility=visibility,
        created_at=datetime.now(UTC),
    )
    db_session.add(bank)
    db_session.commit()
    db_session.refresh(bank)
    return bank


def test_course_service_returns_accessible_owner_course(db_session):
    user = _make_user(db_session, "service_owner")
    bank = _make_bank(db_session, user.id, "Owned")

    service = CourseService(db_session)

    assert service.get_accessible_course(bank.id, user.id).id == bank.id


def test_course_service_hides_private_course_from_other_user(db_session):
    owner = _make_user(db_session, "service_owner_2")
    viewer = _make_user(db_session, "service_viewer_2")
    bank = _make_bank(db_session, owner.id, "Private")

    service = CourseService(db_session)

    with pytest.raises(HTTPException) as exc:
        service.get_accessible_course(bank.id, viewer.id)
    assert exc.value.status_code == 404


def test_course_service_allows_public_course_for_other_user(db_session):
    owner = _make_user(db_session, "service_owner_3")
    viewer = _make_user(db_session, "service_viewer_3")
    bank = _make_bank(db_session, owner.id, "Public", "public")

    service = CourseService(db_session)

    assert service.get_accessible_course(bank.id, viewer.id).id == bank.id
