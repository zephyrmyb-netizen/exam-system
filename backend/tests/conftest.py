"""Pytest fixtures for backend tests."""

import os
import sys
from pathlib import Path

# Ensure the project root is on sys.path so "from backend import ..." works
# regardless of whether pytest runs from project root, backend/, or CI.
_proj_root = Path(__file__).resolve().parent.parent.parent
if str(_proj_root) not in sys.path:
    sys.path.insert(0, str(_proj_root))

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Keep tests independent from a developer's local backend/.env. The app config
# loads backend/.env during import, so these values must be set before importing
# backend modules below.
os.environ["SKIP_DOTENV"] = "1"
os.environ["APP_ENV"] = "development"
os.environ["INVITE_CODE"] = "dev-invite"
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest"

from backend.database import Base, get_db
from backend.main import app

# Use in-memory SQLite for tests — StaticPool keeps a single connection
# so the in-memory database persists across queries.
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign key enforcement on test SQLite connections."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator:
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session) -> Generator:
    """Test client with overridden DB dependency."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function", autouse=True)
def _default_noop_rate_limiter():
    """Inject no-op rate limiters so tests don't hit 429 by default.

    Individual tests that need real rate-limit enforcement can override
    these dependency overrides in their own fixtures.
    """
    from backend.routers.chat import rate_limiter as chat_rl
    from backend.routers.imports import rate_limiter as import_rl

    class _NoLimitLimiter:
        def check(self, *, key, limit, window_s=3600):
            pass

    noop = _NoLimitLimiter()

    app.dependency_overrides[chat_rl] = lambda: noop
    app.dependency_overrides[import_rl] = lambda: noop
    from backend.ratelimit import reset_limiter_for_tests

    reset_limiter_for_tests()
    yield
    # Don't clear here — let the client fixture handle final cleanup.


@pytest.fixture(scope="function")
def auth_headers(client) -> dict:
    """Register and login a test user, return Authorization header."""
    # Register
    client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "password": "testpass123",
            "invite_code": "dev-invite",
        },
    )
    # Login
    resp = client.post(
        "/auth/login",
        json={
            "username": "testuser",
            "password": "testpass123",
        },
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def auth_headers_other(client) -> dict:
    """Second user — for per-user isolation tests (rate limit, visibility)."""
    client.post(
        "/auth/register",
        json={
            "username": "otheruser",
            "password": "otherpass123",
            "invite_code": "dev-invite",
        },
    )
    resp = client.post(
        "/auth/login",
        json={
            "username": "otheruser",
            "password": "otherpass123",
        },
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def sample_questions() -> list[dict]:
    """Sample questions for testing."""
    return [
        {
            "type": "single_choice",
            "question": "1+1=?",
            "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
            "answer": "B",
            "subject": "数学",
            "chapter": "第一章",
        },
        {
            "type": "true_false",
            "question": "地球是圆的",
            "answer": "正确",
            "subject": "地理",
            "chapter": "第一章",
        },
        {
            "type": "multiple_choice",
            "question": "以下哪些是水果？",
            "options": {"A": "苹果", "B": "桌子", "C": "香蕉", "D": "椅子"},
            "answer": "A,C",
            "subject": "常识",
            "chapter": "第二章",
        },
        {
            "type": "fill_blank",
            "question": "中国的首都是___",
            "answer": "北京",
            "subject": "地理",
            "chapter": "第二章",
        },
    ]
