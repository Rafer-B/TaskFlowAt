"""Adiciona os campos de autenticação de dois fatores às contas.

Revision ID: 20261113_0012
Revises: 20261112_0011
Create Date: 2026-11-13
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261113_0012"
down_revision: Union[str, None] = "20261112_0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("two_factor_secret", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "two_factor_enabled",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.add_column(
        "users",
        sa.Column("two_factor_last_used_step", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "two_factor_recovery_codes",
            sa.JSON(),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "two_factor_recovery_codes")
    op.drop_column("users", "two_factor_last_used_step")
    op.drop_column("users", "two_factor_enabled")
    op.drop_column("users", "two_factor_secret")
