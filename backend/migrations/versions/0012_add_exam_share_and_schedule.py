"""Add exam share codes and opening schedule.

Revision ID: 0012
Revises: 0011
Create Date: 2026-07-17
"""

import secrets
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | None = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("exams")}
    with op.batch_alter_table("exams") as batch_op:
        if "share_code" not in columns:
            batch_op.add_column(sa.Column("share_code", sa.String(length=16), nullable=True))
        if "start_at" not in columns:
            batch_op.add_column(sa.Column("start_at", sa.DateTime(), nullable=True))
        if "end_at" not in columns:
            batch_op.add_column(sa.Column("end_at", sa.DateTime(), nullable=True))
    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("exams")}
    if op.f("ix_exams_share_code") not in indexes:
        op.create_index(op.f("ix_exams_share_code"), "exams", ["share_code"], unique=True)
    for exam_id, in bind.execute(sa.text("SELECT id FROM exams WHERE share_code IS NULL")):
        bind.execute(
            sa.text("UPDATE exams SET share_code = :code WHERE id = :id"),
            {"id": exam_id, "code": secrets.token_hex(4).upper()},
        )


def downgrade() -> None:
    with op.batch_alter_table("exams") as batch_op:
        batch_op.drop_index(op.f("ix_exams_share_code"))
        batch_op.drop_column("end_at")
        batch_op.drop_column("start_at")
        batch_op.drop_column("share_code")
