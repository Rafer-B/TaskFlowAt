"""Adiciona papéis de acesso para controlar áreas da aplicação.

Revision ID: 20261102_0003
Revises: 20261030_0002
Create Date: 2026-11-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261102_0003"
down_revision: Union[str, None] = "20261030_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adiciona o papel member como valor inicial das contas existentes."""
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(length=20),
            server_default="member",
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Remove a coluna de papéis."""
    op.drop_column("users", "role")
