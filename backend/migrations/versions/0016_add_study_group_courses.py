"""Track explicitly shared courses without guessing legacy group membership.

Revision ID: 0016
Revises: 0015
"""

import sqlalchemy as sa
from alembic import op

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "study_group_courses" not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table(
            "study_group_courses",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("group_id", sa.Integer(), sa.ForeignKey("study_groups.id", ondelete="CASCADE"), nullable=False),
            sa.Column(
                "course_id", sa.Integer(), sa.ForeignKey("question_banks.id", ondelete="CASCADE"), nullable=False
            ),
            sa.UniqueConstraint("group_id", "course_id", name="uq_study_group_course"),
        )
        op.create_index("ix_study_group_courses_group_id", "study_group_courses", ["group_id"])
        op.create_index("ix_study_group_courses_course_id", "study_group_courses", ["course_id"])
        op.create_index("ix_study_group_courses_id", "study_group_courses", ["id"])


def downgrade() -> None:
    op.drop_table("study_group_courses")
