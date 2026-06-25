from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import DATABASE_URL

_is_sqlite = DATABASE_URL.startswith("sqlite")

_engine_kwargs: dict = {}

if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Production backends (PostgreSQL, MySQL, etc.) benefit from a tuned
    # connection pool. SQLite uses a file lock and doesn't pool connections.
    _engine_kwargs.update(
        pool_size=10,
        max_overflow=20,
        pool_recycle=1800,   # reconnect after 30 min (avoid stale PG conns)
        pool_pre_ping=True,  # verify liveness before returning a conn
    )

engine = create_engine(DATABASE_URL, **_engine_kwargs)

if _is_sqlite:

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        """Enable foreign key enforcement for SQLite connections.

        Without this, ON DELETE CASCADE / SET NULL in table definitions
        are ignored, leading to orphaned rows in practice_records and
        user_question_reviews after a question or course is deleted.
        """
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
