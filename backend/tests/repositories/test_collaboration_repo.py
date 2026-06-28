from datetime import UTC, datetime

from backend import models
from backend.repositories.collaboration_repo import CollaborationRepository


def _make_user(db_session, username: str):
    user = models.User(username=username, password_hash="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _make_course(db_session, owner_id: int, name: str):
    course = models.QuestionBank(owner_id=owner_id, name=name, created_at=datetime.now(UTC))
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)
    return course


def test_collaboration_repo_adds_and_finds_collaborator(db_session):
    owner = _make_user(db_session, "collab_owner")
    collaborator = _make_user(db_session, "collab_user")
    course = _make_course(db_session, owner.id, "Collab Course")
    repo = CollaborationRepository(db_session)

    record = repo.add_collaborator(
        course_id=course.id,
        user_id=collaborator.id,
        role="editor",
        invited_by=owner.id,
    )

    found = repo.find(course.id, collaborator.id)
    assert found is not None
    assert found.id == record.id
    assert found.role == "editor"
    assert found.invited_by == owner.id


def test_collaboration_repo_lists_by_course_and_user(db_session):
    owner = _make_user(db_session, "collab_list_owner")
    user_a = _make_user(db_session, "collab_list_a")
    user_b = _make_user(db_session, "collab_list_b")
    course_a = _make_course(db_session, owner.id, "Course A")
    course_b = _make_course(db_session, owner.id, "Course B")
    repo = CollaborationRepository(db_session)

    first = repo.add_collaborator(course_id=course_a.id, user_id=user_a.id, role="viewer")
    second = repo.add_collaborator(course_id=course_a.id, user_id=user_b.id, role="editor")
    third = repo.add_collaborator(course_id=course_b.id, user_id=user_a.id, role="viewer")

    by_course = repo.get_for_course(course_a.id)
    by_user = repo.get_for_user(user_a.id)

    assert {record.id for record in by_course} == {first.id, second.id}
    assert {record.id for record in by_user} == {first.id, third.id}
