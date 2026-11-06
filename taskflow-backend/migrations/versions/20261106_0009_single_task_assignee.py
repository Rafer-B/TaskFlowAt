"""Limita cada tarefa a um único responsável.

Revision ID: 20261106_0009
Revises: 20261106_0008
Create Date: 2026-11-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261106_0009"
down_revision: Union[str, None] = "20261106_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Preserva a atribuição principal e impõe a cardinalidade na base de dados."""
    op.execute(
        sa.text(
            "DELETE FROM task_assignees AS assignee "
            "USING tasks "
            "WHERE assignee.task_id = tasks.id "
            "AND (tasks.assigned_to IS NULL "
            "OR assignee.user_id <> tasks.assigned_to)"
        )
    )
    op.execute(
        sa.text(
            "INSERT INTO task_assignees (task_id, user_id) "
            "SELECT id, assigned_to FROM tasks "
            "WHERE assigned_to IS NOT NULL "
            "AND NOT EXISTS ("
            "SELECT 1 FROM task_assignees "
            "WHERE task_assignees.task_id = tasks.id"
            ")"
        )
    )
    op.create_unique_constraint(
        "uq_task_assignees_task_id",
        "task_assignees",
        ["task_id"],
    )


def downgrade() -> None:
    """Remove a restrição de um responsável por tarefa."""
    op.drop_constraint(
        "uq_task_assignees_task_id",
        "task_assignees",
        type_="unique",
    )
