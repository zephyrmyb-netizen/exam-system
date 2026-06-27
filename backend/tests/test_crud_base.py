from datetime import UTC, datetime

from backend import models, schemas
from backend.crud_base import GenericCRUD, PaginatedResult


def _create_user(db_session, username="crud-user"):
    user = models.User(username=username, password_hash="hashed")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _create_bank(db_session, owner_id, name="测试题库"):
    bank = models.QuestionBank(
        owner_id=owner_id,
        name=name,
        visibility="private",
        created_at=datetime.now(UTC),
    )
    db_session.add(bank)
    db_session.commit()
    db_session.refresh(bank)
    return bank


def _create_many_banks(db_session, count=5):
    user = _create_user(db_session)
    banks = []
    for index in range(count):
        banks.append(_create_bank(db_session, user.id, f"题库 {index}"))
    return banks


class TestPaginatedResult:
    def test_constructs_with_items_and_total(self):
        result = PaginatedResult(items=[1, 2, 3], total=10, page=1, page_size=3)

        assert result.items == [1, 2, 3]
        assert result.total == 10
        assert result.page == 1
        assert result.page_size == 3

    def test_total_pages_rounds_up(self):
        result = PaginatedResult(items=[1], total=10, page=4, page_size=3)

        assert result.total_pages == 4

    def test_total_pages_zero_when_empty(self):
        result = PaginatedResult(items=[], total=0, page=1, page_size=20)

        assert result.total_pages == 0

    def test_has_next_and_has_prev(self):
        first_page = PaginatedResult(items=[1], total=10, page=1, page_size=3)
        last_page = PaginatedResult(items=[1], total=10, page=4, page_size=3)

        assert first_page.has_next is True
        assert first_page.has_prev is False
        assert last_page.has_next is False
        assert last_page.has_prev is True


class TestGenericCRUD:
    def test_get_by_id_returns_model_instance(self, db_session):
        user = _create_user(db_session)
        bank = _create_bank(db_session, user.id)
        repo = GenericCRUD(models.QuestionBank, schemas.CourseCreate, schemas.CourseUpdate)

        result = repo.get_by_id(db_session, bank.id)

        assert result is not None
        assert result.id == bank.id

    def test_get_by_id_returns_none_when_missing(self, db_session):
        repo = GenericCRUD(models.QuestionBank, schemas.CourseCreate, schemas.CourseUpdate)

        assert repo.get_by_id(db_session, 999999) is None

    def test_paginate_applies_offset_and_limit(self, db_session):
        banks = _create_many_banks(db_session)
        repo = GenericCRUD(models.QuestionBank, schemas.CourseCreate, schemas.CourseUpdate)

        result = repo.paginate(db_session, page=1, page_size=2)

        assert len(result.items) == 2
        assert result.total == len(banks)
        assert result.total_pages == 3

    def test_paginate_page_zero_returns_all(self, db_session):
        banks = _create_many_banks(db_session)
        repo = GenericCRUD(models.QuestionBank, schemas.CourseCreate, schemas.CourseUpdate)

        result = repo.paginate(db_session, page=0, page_size=0)

        assert len(result.items) == len(banks)
        assert result.total == len(banks)
