"""Add Phase 2 architecture tables.

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-27
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_roles_id"), "roles", ["id"], unique=False)
    op.create_index(op.f("ix_roles_name"), "roles", ["name"], unique=True)

    op.add_column("users", sa.Column("role_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_users_role_id"), "users", ["role_id"], unique=False)

    op.create_table(
        "exams",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("creator_id", sa.Integer(), nullable=False),
        sa.Column("time_limit", sa.Integer(), nullable=False),
        sa.Column("total_score", sa.Integer(), nullable=False),
        sa.Column("is_shuffle", sa.Integer(), nullable=False),
        sa.Column("is_blind", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["question_banks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_exams_id"), "exams", ["id"], unique=False)
    op.create_index(op.f("ix_exams_course_id"), "exams", ["course_id"], unique=False)
    op.create_index(op.f("ix_exams_creator_id"), "exams", ["creator_id"], unique=False)
    op.create_index(op.f("ix_exams_status"), "exams", ["status"], unique=False)

    op.create_table(
        "collaborations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("invited_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["question_banks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invited_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id", "user_id", name="uq_course_user_collab"),
    )
    op.create_index(op.f("ix_collaborations_id"), "collaborations", ["id"], unique=False)
    op.create_index(op.f("ix_collaborations_course_id"), "collaborations", ["course_id"], unique=False)
    op.create_index(op.f("ix_collaborations_user_id"), "collaborations", ["user_id"], unique=False)

    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("color", sa.String(length=20), nullable=True),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["parent_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tags_id"), "tags", ["id"], unique=False)
    op.create_index(op.f("ix_tags_name"), "tags", ["name"], unique=False)
    op.create_index(op.f("ix_tags_parent_id"), "tags", ["parent_id"], unique=False)

    op.create_table(
        "exam_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("exam_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_exam_questions_id"), "exam_questions", ["id"], unique=False)
    op.create_index(op.f("ix_exam_questions_exam_id"), "exam_questions", ["exam_id"], unique=False)
    op.create_index(op.f("ix_exam_questions_question_id"), "exam_questions", ["question_id"], unique=False)

    op.create_table(
        "exam_submissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("exam_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("is_passed", sa.Integer(), nullable=False),
        sa.Column("answers", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_exam_submissions_id"), "exam_submissions", ["id"], unique=False)
    op.create_index(op.f("ix_exam_submissions_exam_id"), "exam_submissions", ["exam_id"], unique=False)
    op.create_index(op.f("ix_exam_submissions_user_id"), "exam_submissions", ["user_id"], unique=False)

    op.create_table(
        "question_tags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("question_id", "tag_id", name="uq_question_tag"),
    )
    op.create_index(op.f("ix_question_tags_id"), "question_tags", ["id"], unique=False)
    op.create_index(op.f("ix_question_tags_question_id"), "question_tags", ["question_id"], unique=False)
    op.create_index(op.f("ix_question_tags_tag_id"), "question_tags", ["tag_id"], unique=False)

    op.create_table(
        "bookmarks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("folder_name", sa.String(length=100), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "question_id", name="uq_user_question_bookmark"),
    )
    op.create_index(op.f("ix_bookmarks_id"), "bookmarks", ["id"], unique=False)
    op.create_index(op.f("ix_bookmarks_user_id"), "bookmarks", ["user_id"], unique=False)
    op.create_index(op.f("ix_bookmarks_question_id"), "bookmarks", ["question_id"], unique=False)

    op.create_table(
        "study_goals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("target_count", sa.Integer(), nullable=False),
        sa.Column("deadline", sa.DateTime(), nullable=True),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_study_goals_id"), "study_goals", ["id"], unique=False)
    op.create_index(op.f("ix_study_goals_user_id"), "study_goals", ["user_id"], unique=False)

    roles = sa.table("roles", sa.column("id", sa.Integer), sa.column("name", sa.String))
    op.bulk_insert(
        roles,
        [
            {"id": 1, "name": "student"},
            {"id": 2, "name": "teacher"},
            {"id": 3, "name": "admin"},
        ],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_study_goals_user_id"), table_name="study_goals")
    op.drop_index(op.f("ix_study_goals_id"), table_name="study_goals")
    op.drop_table("study_goals")

    op.drop_index(op.f("ix_bookmarks_question_id"), table_name="bookmarks")
    op.drop_index(op.f("ix_bookmarks_user_id"), table_name="bookmarks")
    op.drop_index(op.f("ix_bookmarks_id"), table_name="bookmarks")
    op.drop_table("bookmarks")

    op.drop_index(op.f("ix_question_tags_tag_id"), table_name="question_tags")
    op.drop_index(op.f("ix_question_tags_question_id"), table_name="question_tags")
    op.drop_index(op.f("ix_question_tags_id"), table_name="question_tags")
    op.drop_table("question_tags")

    op.drop_index(op.f("ix_exam_submissions_user_id"), table_name="exam_submissions")
    op.drop_index(op.f("ix_exam_submissions_exam_id"), table_name="exam_submissions")
    op.drop_index(op.f("ix_exam_submissions_id"), table_name="exam_submissions")
    op.drop_table("exam_submissions")

    op.drop_index(op.f("ix_exam_questions_question_id"), table_name="exam_questions")
    op.drop_index(op.f("ix_exam_questions_exam_id"), table_name="exam_questions")
    op.drop_index(op.f("ix_exam_questions_id"), table_name="exam_questions")
    op.drop_table("exam_questions")

    op.drop_index(op.f("ix_tags_parent_id"), table_name="tags")
    op.drop_index(op.f("ix_tags_name"), table_name="tags")
    op.drop_index(op.f("ix_tags_id"), table_name="tags")
    op.drop_table("tags")

    op.drop_index(op.f("ix_collaborations_user_id"), table_name="collaborations")
    op.drop_index(op.f("ix_collaborations_course_id"), table_name="collaborations")
    op.drop_index(op.f("ix_collaborations_id"), table_name="collaborations")
    op.drop_table("collaborations")

    op.drop_index(op.f("ix_exams_status"), table_name="exams")
    op.drop_index(op.f("ix_exams_creator_id"), table_name="exams")
    op.drop_index(op.f("ix_exams_course_id"), table_name="exams")
    op.drop_index(op.f("ix_exams_id"), table_name="exams")
    op.drop_table("exams")

    op.drop_index(op.f("ix_users_role_id"), table_name="users")
    op.drop_column("users", "role_id")

    op.drop_index(op.f("ix_roles_name"), table_name="roles")
    op.drop_index(op.f("ix_roles_id"), table_name="roles")
    op.drop_table("roles")
