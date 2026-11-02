"""Add contributor and viewer roles to project memberships.

Revision ID: 20261102_0005
Revises: 20261102_0004
Create Date: 2026-11-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261102_0005"
down_revision: Union[str, None] = "20261102_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE project_members "
        "DROP CONSTRAINT IF EXISTS project_members_role_check"
    )
    op.execute(
        "ALTER TABLE project_members "
        "DROP CONSTRAINT IF EXISTS ck_project_members_role"
    )
    op.execute(
        sa.text(
            "UPDATE project_members SET role = 'contributor' "
            "WHERE role = 'member'"
        )
    )
    op.alter_column(
        "project_members",
        "role",
        existing_type=sa.String(length=20),
        server_default="contributor",
    )
    op.create_check_constraint(
        "ck_project_members_role",
        "project_members",
        "role IN ('owner', 'contributor', 'viewer')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_project_members_role",
        "project_members",
        type_="check",
    )
    op.execute(
        sa.text(
            "UPDATE project_members SET role = 'member' "
            "WHERE role = 'contributor'"
        )
    )
    op.alter_column(
        "project_members",
        "role",
        existing_type=sa.String(length=20),
        server_default="member",
    )
