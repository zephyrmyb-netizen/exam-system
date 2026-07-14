from fastapi import HTTPException

from backend import models
from backend.services.permission_service import PermissionService


def _make_user(db_session, username: str, role_name: str | None = None) -> models.User:
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


def test_user_with_no_role_defaults_student(db_session):
    user = _make_user(db_session, "student_default")
    service = PermissionService(db_session)

    assert service.get_role_name(user) == "student"


def test_student_can_practice_and_create_course(db_session):
    user = _make_user(db_session, "student_user")
    service = PermissionService(db_session)

    assert service.can(user, "practice:random") is True
    assert service.can(user, "course:create") is True


def test_student_cannot_create_exam(db_session):
    user = _make_user(db_session, "student_no_exam")
    service = PermissionService(db_session)

    assert service.can(user, "exam:create") is False


def test_teacher_can_create_exam(db_session):
    user = _make_user(db_session, "teacher_user", "teacher")
    service = PermissionService(db_session)

    assert service.can(user, "exam:create") is True


def test_admin_can_manage_users(db_session):
    user = _make_user(db_session, "admin_user", "admin")
    service = PermissionService(db_session)

    assert service.can(user, "user:manage") is True


def test_assert_can_raises_403_when_denied(db_session):
    user = _make_user(db_session, "student_denied")
    service = PermissionService(db_session)

    try:
        service.assert_can(user, "user:manage")
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("Expected HTTPException")
