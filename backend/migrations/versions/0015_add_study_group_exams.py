"""Add explicit shared exams for study groups.

Revision ID: 0015
Revises: 0014
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | None = None


def upgrade() -> None:
    if "study_group_exams" not in set(sa.inspect(op.get_bind()).get_table_names()):
        op.create_table(
            "study_group_exams",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("group_id", sa.Integer(), sa.ForeignKey("study_groups.id", ondelete="CASCADE"), nullable=False),
            sa.Column("exam_id", sa.Integer(), sa.ForeignKey("exams.id", ondelete="CASCADE"), nullable=False),
            sa.UniqueConstraint("group_id", "exam_id", name="uq_study_group_exam"),
        )


def downgrade() -> None:
    op.drop_table("study_group_exams")
