"""Add private course share tokens.

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | None = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("question_banks")}
    if "share_token" not in columns:
        with op.batch_alter_table("question_banks") as batch_op:
            batch_op.add_column(sa.Column("share_token", sa.String(length=64), nullable=True))

    indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("question_banks")}
    index_name = op.f("ix_question_banks_share_token")
    if index_name not in indexes:
        op.create_index(index_name, "question_banks", ["share_token"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("question_banks") as batch_op:
        batch_op.drop_index(op.f("ix_question_banks_share_token"))
        batch_op.drop_column("share_token")
