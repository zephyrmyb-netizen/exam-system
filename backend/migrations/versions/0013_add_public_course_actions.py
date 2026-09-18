"""Add public course favorites and reports.

Revision ID: 0013
Revises: 0012
Create Date: 2026-07-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "course_favorites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("question_banks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("course_id", "user_id", name="uq_course_favorite_user"),
    )
    op.create_index(op.f("ix_course_favorites_course_id"), "course_favorites", ["course_id"])
    op.create_index(op.f("ix_course_favorites_user_id"), "course_favorites", ["user_id"])
    op.create_table(
        "course_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("question_banks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reporter_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reason", sa.String(length=80), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_course_reports_course_id"), "course_reports", ["course_id"])
    op.create_index(op.f("ix_course_reports_reporter_id"), "course_reports", ["reporter_id"])
    op.create_index(op.f("ix_course_reports_status"), "course_reports", ["status"])


def downgrade() -> None:
    op.drop_table("course_reports")
    op.drop_table("course_favorites")
