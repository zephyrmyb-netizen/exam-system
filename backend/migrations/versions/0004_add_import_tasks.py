"""Add durable AI import tasks.

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "import_tasks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("source_filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("course_id", sa.Integer(), nullable=True),
        sa.Column("course_name", sa.String(length=200), nullable=False),
        sa.Column("progress_current", sa.Integer(), nullable=False),
        sa.Column("progress_total", sa.Integer(), nullable=False),
        sa.Column("preview_questions_json", sa.Text(), nullable=True),
        sa.Column("warnings_json", sa.Text(), nullable=True),
        sa.Column("timing_json", sa.Text(), nullable=True),
        sa.Column("total_valid", sa.Integer(), nullable=False),
        sa.Column("total_invalid", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["course_id"], ["question_banks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_import_tasks_id"), "import_tasks", ["id"], unique=False)
    op.create_index(op.f("ix_import_tasks_owner_id"), "import_tasks", ["owner_id"], unique=False)
    op.create_index(op.f("ix_import_tasks_status"), "import_tasks", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_import_tasks_status"), table_name="import_tasks")
    op.drop_index(op.f("ix_import_tasks_owner_id"), table_name="import_tasks")
    op.drop_index(op.f("ix_import_tasks_id"), table_name="import_tasks")
    op.drop_table("import_tasks")
