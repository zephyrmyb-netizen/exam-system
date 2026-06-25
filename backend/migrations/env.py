"""Alembic environment config — reads DATABASE_URL from backend/.env."""
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Ensure the project root is on sys.path so "from backend import ..." works.
_proj_root = Path(__file__).resolve().parent.parent.parent
if str(_proj_root) not in sys.path:
    sys.path.insert(0, str(_proj_root))

# Load .env before importing backend.config (which reads os.environ).
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path, encoding="utf-8-sig")

from backend.config import DATABASE_URL
from backend.database import Base
from backend import models  # noqa: F401 — ensure all models are imported

config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
