"""Add status and reply fields to feedback entries.

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("feedback_entries")}
    if {"status", "admin_reply", "updated_at"} - columns:
        with op.batch_alter_table("feedback_entries") as batch_op:
            if "status" not in columns:
                batch_op.add_column(sa.Column("status", sa.String(length=20), nullable=False, server_default="new"))
            if "admin_reply" not in columns:
                batch_op.add_column(sa.Column("admin_reply", sa.Text(), nullable=False, server_default=""))
            if "updated_at" not in columns:
                batch_op.add_column(sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))

    indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("feedback_entries")}
    if op.f("ix_feedback_entries_status") not in indexes:
        op.create_index(op.f("ix_feedback_entries_status"), "feedback_entries", ["status"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("feedback_entries") as batch_op:
        batch_op.drop_index(op.f("ix_feedback_entries_status"))
        batch_op.drop_column("updated_at")
        batch_op.drop_column("admin_reply")
        batch_op.drop_column("status")
