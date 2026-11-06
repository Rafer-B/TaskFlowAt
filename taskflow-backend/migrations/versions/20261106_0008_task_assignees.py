"""Cria uma associação persistente entre tarefas e responsáveis.

Revision ID: 20261106_0008
Revises: 20261102_0007
Create Date: 2026-11-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261106_0008"
down_revision: Union[str, None] = "20261102_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria a associação e migra os responsáveis existentes."""
    op.create_table(
        "task_assignees",
        sa.Column("task_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("task_id", "user_id"),
    )
    op.execute(
        sa.text(
            "INSERT INTO task_assignees (task_id, user_id) "
            "SELECT id, assigned_to FROM tasks WHERE assigned_to IS NOT NULL"
        )
    )


def downgrade() -> None:
    """Remove a associação múltipla, mantendo o responsável legado."""
    op.drop_table("task_assignees")
