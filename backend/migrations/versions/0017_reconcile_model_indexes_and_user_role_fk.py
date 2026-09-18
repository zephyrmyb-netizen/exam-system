"""Reconcile model-declared indexes and the users.role_id foreign key.

Phase 3/4 model changes (study groups, public course actions, exam
scheduling) declared `index=True` columns and the users.role_id FK without
matching migrations. This revision closes the drift so `alembic check`
passes and CI can gate on it:

- add the missing per-column indexes (SQLite CREATE INDEX, no table rebuild);
- add the users.role_id -> roles.id FK (batch mode: SQLite cannot ALTER
  TABLE ADD CONSTRAINT);
- drop three legacy composite indexes that models no longer declare.

Revision ID: 0017
Revises: 0016
Create Date: 2026-09-18
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Indexes declared on models but missing from the migration chain.
    op.create_index("ix_course_favorites_id", "course_favorites", ["id"], unique=False)
    op.create_index("ix_course_reports_id", "course_reports", ["id"], unique=False)
    op.create_index("ix_exams_end_at", "exams", ["end_at"], unique=False)
    op.create_index("ix_exams_start_at", "exams", ["start_at"], unique=False)
    op.create_index("ix_study_group_exams_exam_id", "study_group_exams", ["exam_id"], unique=False)
    op.create_index("ix_study_group_exams_group_id", "study_group_exams", ["group_id"], unique=False)
    op.create_index("ix_study_group_exams_id", "study_group_exams", ["id"], unique=False)
    op.create_index("ix_study_group_members_group_id", "study_group_members", ["group_id"], unique=False)
    op.create_index("ix_study_group_members_id", "study_group_members", ["id"], unique=False)
    op.create_index("ix_study_group_members_user_id", "study_group_members", ["user_id"], unique=False)
    op.create_index("ix_study_groups_id", "study_groups", ["id"], unique=False)
    op.create_index("ix_study_groups_invite_code", "study_groups", ["invite_code"], unique=True)
    op.create_index("ix_study_groups_owner_id", "study_groups", ["owner_id"], unique=False)

    # users.role_id -> roles.id (batch mode recreates the table on SQLite).
    with op.batch_alter_table("users") as batch_op:
        batch_op.create_foreign_key("fk_users_role_id_roles", "roles", ["role_id"], ["id"], ondelete="SET NULL")

    # Legacy composite indexes superseded by per-column indexes on models.
    op.drop_index("ix_practice_records_user_answered", table_name="practice_records")
    op.drop_index("ix_user_question_reviews_user_next_review", table_name="user_question_reviews")
    op.drop_index("ix_wrong_records_user_question", table_name="wrong_records")


def downgrade() -> None:
    op.create_index(
        "ix_practice_records_user_answered",
        "practice_records",
        ["user_id", "answered_at"],
        unique=False,
    )
    op.create_index(
        "ix_user_question_reviews_user_next_review",
        "user_question_reviews",
        ["user_id", "next_review_at"],
        unique=False,
    )
    op.create_index(
        "ix_wrong_records_user_question",
        "wrong_records",
        ["user_id", "question_id"],
        unique=False,
    )

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("fk_users_role_id_roles", type_="foreignkey")

    op.drop_index("ix_study_groups_owner_id", table_name="study_groups")
    op.drop_index("ix_study_groups_invite_code", table_name="study_groups")
    op.drop_index("ix_study_groups_id", table_name="study_groups")
    op.drop_index("ix_study_group_members_user_id", table_name="study_group_members")
    op.drop_index("ix_study_group_members_id", table_name="study_group_members")
    op.drop_index("ix_study_group_members_group_id", table_name="study_group_members")
    op.drop_index("ix_study_group_exams_id", table_name="study_group_exams")
    op.drop_index("ix_study_group_exams_group_id", table_name="study_group_exams")
    op.drop_index("ix_study_group_exams_exam_id", table_name="study_group_exams")
    op.drop_index("ix_exams_start_at", table_name="exams")
    op.drop_index("ix_exams_end_at", table_name="exams")
    op.drop_index("ix_course_reports_id", table_name="course_reports")
    op.drop_index("ix_course_favorites_id", table_name="course_favorites")
