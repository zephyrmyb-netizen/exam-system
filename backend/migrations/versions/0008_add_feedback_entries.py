"""Add persistent help and feedback entries.

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "feedback_entries" in inspector.get_table_names():
        existing_indexes = {index["name"] for index in inspector.get_indexes("feedback_entries")}
        for index_name, columns in (
            (op.f("ix_feedback_entries_id"), ["id"]),
            (op.f("ix_feedback_entries_user_id"), ["user_id"]),
            (op.f("ix_feedback_entries_created_at"), ["created_at"]),
        ):
            if index_name not in existing_indexes:
                op.create_index(index_name, "feedback_entries", columns, unique=False)
        return

    op.create_table(
        "feedback_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False, server_default="suggestion"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("contact", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_feedback_entries_id"), "feedback_entries", ["id"], unique=False)
    op.create_index(op.f("ix_feedback_entries_user_id"), "feedback_entries", ["user_id"], unique=False)
    op.create_index(op.f("ix_feedback_entries_created_at"), "feedback_entries", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_feedback_entries_created_at"), table_name="feedback_entries")
    op.drop_index(op.f("ix_feedback_entries_user_id"), table_name="feedback_entries")
    op.drop_index(op.f("ix_feedback_entries_id"), table_name="feedback_entries")
    op.drop_table("feedback_entries")
