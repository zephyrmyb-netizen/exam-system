"""Pre-generate share tokens so sharing does not wait for a network write.

Revision ID: 0011
Revises: 0010
Create Date: 2026-07-17
"""

import secrets
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | None = None


def upgrade() -> None:
    bind = op.get_bind()
    course_ids = [row[0] for row in bind.execute(sa.text("SELECT id FROM question_banks WHERE share_token IS NULL"))]
    for course_id in course_ids:
        bind.execute(
            sa.text("UPDATE question_banks SET share_token = :token WHERE id = :course_id"),
            {"token": secrets.token_urlsafe(32), "course_id": course_id},
        )


def downgrade() -> None:
    # Tokens are generated secrets; do not erase live links during a downgrade.
    pass
