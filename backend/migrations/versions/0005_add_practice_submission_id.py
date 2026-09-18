"""Add idempotency keys for offline practice submissions.

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    column_names = {column["name"] for column in inspector.get_columns("practice_records")}
    has_submission_key = "client_submission_id" in column_names
    has_unique_constraint = any(
        constraint.get("column_names") == ["user_id", "client_submission_id"]
        for constraint in inspector.get_unique_constraints("practice_records")
    )

    if has_submission_key and has_unique_constraint:
        return

    with op.batch_alter_table("practice_records") as batch_op:
        if not has_submission_key:
            batch_op.add_column(sa.Column("client_submission_id", sa.String(length=64), nullable=True))
        if not has_unique_constraint:
            batch_op.create_unique_constraint(
                "uq_practice_records_user_submission",
                ["user_id", "client_submission_id"],
            )


def downgrade() -> None:
    with op.batch_alter_table("practice_records") as batch_op:
        batch_op.drop_constraint("uq_practice_records_user_submission", type_="unique")
        batch_op.drop_column("client_submission_id")
