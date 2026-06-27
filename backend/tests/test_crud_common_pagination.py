from datetime import UTC, datetime

from backend import models
from backend.crud_common import apply_pagination


def _create_user(db_session):
    user = models.User(username="pagination-user", password_hash="hashed")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _create_banks(db_session, count=5):
    user = _create_user(db_session)
    banks = []
    for index in range(count):
        bank = models.QuestionBank(
            owner_id=user.id,
            name=f"分页题库 {index}",
            visibility="private",
            created_at=datetime.now(UTC),
        )
        db_session.add(bank)
        banks.append(bank)
    db_session.commit()
    return banks


def test_apply_pagination_limits_items_and_returns_total(db_session):
    banks = _create_banks(db_session)
    query = db_session.query(models.QuestionBank).order_by(models.QuestionBank.id.asc())

    items, total = apply_pagination(query, page=1, page_size=2)

    assert total == len(banks)
    assert len(items) == 2
    assert items[0].name == "分页题库 0"


def test_apply_pagination_returns_all_when_page_is_zero(db_session):
    banks = _create_banks(db_session)
    query = db_session.query(models.QuestionBank).order_by(models.QuestionBank.id.asc())

    items, total = apply_pagination(query, page=0, page_size=0)

    assert total == len(banks)
    assert len(items) == len(banks)
