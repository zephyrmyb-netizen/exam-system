"""Add image_urls, display_name, is_guest columns.

These columns exist in models.py but were missing from Alembic migrations.
Previously only SQLite got them via ensure_runtime_schema() runtime patch,
which left PostgreSQL deployments broken.

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    question_columns = {column["name"] for column in inspector.get_columns("questions")}
    user_columns = {column["name"] for column in inspector.get_columns("users")}

    if "image_urls" not in question_columns:
        with op.batch_alter_table("questions") as batch_op:
            batch_op.add_column(
                sa.Column("image_urls", sa.Text(), nullable=False, server_default="[]")
            )

    if {"display_name", "is_guest"} - user_columns:
        with op.batch_alter_table("users") as batch_op:
            if "display_name" not in user_columns:
                batch_op.add_column(
                    sa.Column("display_name", sa.String(length=100), nullable=False, server_default="")
                )
            if "is_guest" not in user_columns:
                batch_op.add_column(
                    sa.Column("is_guest", sa.Integer(), nullable=False, server_default="0")
                )

    user_indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("users")}
    if op.f("ix_users_is_guest") not in user_indexes:
        op.create_index(op.f("ix_users_is_guest"), "users", ["is_guest"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_index(op.f("ix_users_is_guest"))
        batch_op.drop_column("is_guest")
        batch_op.drop_column("display_name")

    with op.batch_alter_table("questions") as batch_op:
        batch_op.drop_column("image_urls")
