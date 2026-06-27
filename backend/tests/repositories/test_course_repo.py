from datetime import UTC, datetime

from backend import models
from backend.repositories.course_repo import CourseRepository


def _make_user(db_session, username: str = "repo_user") -> models.User:
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


def test_course_repository_get_by_id_returns_bank(db_session):
    user = _make_user(db_session)
    bank = _make_bank(db_session, user.id, "Repo Course")

    repo = CourseRepository(db_session)

    assert repo.get_by_id(bank.id).id == bank.id
    assert repo.get_by_id(999999) is None


def test_course_repository_visible_filters_private_courses(db_session):
    owner = _make_user(db_session, "repo_owner")
    viewer = _make_user(db_session, "repo_viewer")
    private = _make_bank(db_session, owner.id, "Private", "private")
    public = _make_bank(db_session, owner.id, "Public", "public")

    repo = CourseRepository(db_session)
    banks, total = repo.get_visible(user_id=viewer.id)

    ids = {bank.id for bank in banks}
    assert public.id in ids
    assert private.id not in ids
    assert total == 1


def test_course_repository_owned_only_returns_owner_courses(db_session):
    owner = _make_user(db_session, "repo_owner_2")
    other = _make_user(db_session, "repo_other_2")
    owned = _make_bank(db_session, owner.id, "Owned", "private")
    _make_bank(db_session, other.id, "Other", "public")

    repo = CourseRepository(db_session)
    banks, total = repo.get_owned(owner_id=owner.id)

    assert total == 1
    assert [bank.id for bank in banks] == [owned.id]
