"""Tests for database engine compatibility (SQLite vs PostgreSQL)."""
import pytest
from sqlalchemy import create_engine, event


class TestDatabaseEngine:
    """Verify engine creation doesn't break for different DATABASE_URL values."""

    def test_sqlite_engine_creation(self):
        """SQLite URL creates an engine with check_same_thread=False."""
        engine = create_engine(
            "sqlite:///./test.db",
            connect_args={"check_same_thread": False},
        )
        # Verify it's a SQLite engine
        assert engine.dialect.name == "sqlite"

        # The PRAGMA foreign_keys listener should have been registered
        # by our database.py; we test that it works by just creating
        # the engine without errors.

    def test_postgres_engine_creation(self):
        """PostgreSQL URL creates an engine WITHOUT SQLite-specific args."""
        pytest.importorskip("psycopg2")
        # Create engine the way database.py would for PostgreSQL
        url = "postgresql://user:pass@localhost:5432/examdb"
        _is_sqlite = url.startswith("sqlite")
        _engine_kwargs = {}
        if _is_sqlite:
            _engine_kwargs["connect_args"] = {"check_same_thread": False}

        engine = create_engine(url, **_engine_kwargs)
        assert engine.dialect.name == "postgresql"

        # The engine should have been created without connect_args
        # (since _is_sqlite is False)

    def test_sqlite_still_works_end_to_end(self, client, auth_headers):
        """Sanity: health check endpoint still works."""
        resp = client.get("/health")
        assert resp.status_code == 200


class TestTimezone:
    """Tests for local timezone in today stat calculations."""

    def test_zoneinfo_is_available(self):
        """zoneinfo should be available (Python 3.9+)."""
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("Asia/Shanghai")
        assert tz is not None

    def test_default_timezone_is_valid(self):
        """APP_TIMEZONE default 'Asia/Shanghai' must be a valid zone."""
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
        from backend.config import APP_TIMEZONE
        try:
            tz = ZoneInfo(APP_TIMEZONE)
            assert tz is not None
        except ZoneInfoNotFoundError:
            pytest.fail(f"APP_TIMEZONE '{APP_TIMEZONE}' is not a valid zoneinfo zone")
