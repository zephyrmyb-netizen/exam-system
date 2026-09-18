"""Collapse legacy teacher roles into standard users.

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _role_id(connection, name: str) -> int | None:
    return connection.execute(sa.text("SELECT id FROM roles WHERE name = :name"), {"name": name}).scalar()


def upgrade() -> None:
    connection = op.get_bind()
    student_role_id = _role_id(connection, "student")
    if student_role_id is None:
        connection.execute(sa.text("INSERT INTO roles (name) VALUES (:name)"), {"name": "student"})
        student_role_id = _role_id(connection, "student")

    teacher_role_id = _role_id(connection, "teacher")
    if teacher_role_id is None:
        return

    connection.execute(
        sa.text("UPDATE users SET role_id = :student_role_id WHERE role_id = :teacher_role_id"),
        {"student_role_id": student_role_id, "teacher_role_id": teacher_role_id},
    )
    connection.execute(sa.text("DELETE FROM roles WHERE id = :role_id"), {"role_id": teacher_role_id})


def downgrade() -> None:
    # Role removal is intentionally irreversible: a previous teacher assignment
    # no longer represents a supported product role.
    pass
