"""Tracks the enabled 2FA methods separately.

Revision ID: 20261115_0015
Revises: 20261113_0014
Create Date: 2026-11-15
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261115_0015"
down_revision: Union[str, None] = "20261113_0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "two_factor_email_enabled",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "two_factor_authenticator_enabled",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.execute(
        sa.text(
            "UPDATE users SET two_factor_authenticator_enabled = true "
            "WHERE two_factor_enabled = true AND two_factor_secret IS NOT NULL"
        )
    )


def downgrade() -> None:
    op.drop_column("users", "two_factor_authenticator_enabled")
    op.drop_column("users", "two_factor_email_enabled")
