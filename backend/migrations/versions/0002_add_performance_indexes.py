"""Add performance indexes for practice and review queries.

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-25
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # practice_records: (user_id, answered_at) for stats queries
    op.create_index(
        "ix_practice_records_user_answered",
        "practice_records",
        ["user_id", "answered_at"],
        unique=False,
    )

    # user_question_reviews: (user_id, next_review_at) for due-review queries
    op.create_index(
        "ix_user_question_reviews_user_next_review",
        "user_question_reviews",
        ["user_id", "next_review_at"],
        unique=False,
    )

    # wrong_records: composite on (user_id, question_id) for fast upsert/delete
    op.create_index(
        "ix_wrong_records_user_question",
        "wrong_records",
        ["user_id", "question_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_wrong_records_user_question", table_name="wrong_records")
    op.drop_index("ix_user_question_reviews_user_next_review", table_name="user_question_reviews")
    op.drop_index("ix_practice_records_user_answered", table_name="practice_records")
