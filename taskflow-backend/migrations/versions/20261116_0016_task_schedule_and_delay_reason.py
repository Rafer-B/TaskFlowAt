"""Add planned task start dates and delay justifications.

Revision ID: 20261116_0016
Revises: 20261115_0015
Create Date: 2026-11-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261116_0016"
down_revision: Union[str, None] = "20261115_0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "tasks",
        sa.Column("delay_reason", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tasks", "delay_reason")
    op.drop_column("tasks", "start_date")
