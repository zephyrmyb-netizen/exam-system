"""Initial baseline — all tables from models.py.

Revision ID: 0001
Revises: None
Create Date: 2026-06-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    op.create_table(
        "question_banks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("subject", sa.String(200), nullable=True),
        sa.Column("visibility", sa.String(20), nullable=False, server_default="private"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_question_banks_id"), "question_banks", ["id"], unique=False)
    op.create_index(op.f("ix_question_banks_owner_id"), "question_banks", ["owner_id"], unique=False)
    op.create_index(op.f("ix_question_banks_visibility"), "question_banks", ["visibility"], unique=False)

    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=True),
        sa.Column("course_id", sa.Integer(), nullable=True),
        sa.Column("visibility", sa.String(20), nullable=False, server_default="private"),
        sa.Column("source", sa.String(20), nullable=False, server_default="import"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("subject", sa.String(200), nullable=True),
        sa.Column("chapter", sa.String(200), nullable=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("options", sa.Text(), nullable=True),
        sa.Column("answer", sa.String(500), nullable=False),
        sa.Column("analysis", sa.Text(), nullable=True),
        sa.Column("difficulty", sa.String(20), nullable=True),
        sa.ForeignKeyConstraint(["course_id"], ["question_banks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_questions_id"), "questions", ["id"], unique=False)
    op.create_index(op.f("ix_questions_owner_id"), "questions", ["owner_id"], unique=False)
    op.create_index(op.f("ix_questions_course_id"), "questions", ["course_id"], unique=False)
    op.create_index(op.f("ix_questions_visibility"), "questions", ["visibility"], unique=False)

    op.create_table(
        "wrong_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("wrong_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_wrong_answer", sa.String(500), nullable=True),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_wrong_records_id"), "wrong_records", ["id"], unique=False)

    op.create_table(
        "practice_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=True),
        sa.Column("course_id", sa.Integer(), nullable=True),
        sa.Column("question_type", sa.String(50), nullable=True),
        sa.Column("is_correct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("user_answer", sa.String(500), nullable=True),
        sa.Column("correct_answer", sa.String(500), nullable=True),
        sa.Column("answered_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["question_banks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_practice_records_id"), "practice_records", ["id"], unique=False)
    op.create_index(op.f("ix_practice_records_user_id"), "practice_records", ["user_id"], unique=False)
    op.create_index(op.f("ix_practice_records_question_id"), "practice_records", ["question_id"], unique=False)

    op.create_table(
        "user_question_reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=True),
        sa.Column("course_id", sa.Integer(), nullable=True),
        sa.Column("last_reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("next_review_at", sa.DateTime(), nullable=True),
        sa.Column("review_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("review_mode", sa.String(20), nullable=True),
        sa.Column("consecutive_correct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("consecutive_wrong", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["question_banks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "question_id", name="uq_user_question_review"),
    )
    op.create_index(op.f("ix_user_question_reviews_id"), "user_question_reviews", ["id"], unique=False)
    op.create_index(op.f("ix_user_question_reviews_user_id"), "user_question_reviews", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_user_question_reviews_question_id"), "user_question_reviews", ["question_id"], unique=False
    )
    op.create_index(
        op.f("ix_user_question_reviews_next_review_at"), "user_question_reviews", ["next_review_at"], unique=False
    )


def downgrade() -> None:
    op.drop_table("user_question_reviews")
    op.drop_table("practice_records")
    op.drop_table("wrong_records")
    op.drop_table("questions")
    op.drop_table("question_banks")
    op.drop_table("users")
