"""Create persistent calendar events.

Revision ID: 20261102_0006
Revises: 20261102_0005
Create Date: 2026-11-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261102_0006"
down_revision: Union[str, None] = "20261102_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "calendar_events",
        sa.Column(
            "id",
            sa.BigInteger(),
            sa.Identity(always=True),
            nullable=False,
        ),
        sa.Column("project_id", sa.BigInteger(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "color",
            sa.String(length=20),
            server_default="purple",
            nullable=False,
        ),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "end_at > start_at",
            name="ck_calendar_events_end_after_start",
        ),
        sa.CheckConstraint(
            "color IN ('blue', 'purple', 'green', 'red')",
            name="ck_calendar_events_color",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_calendar_events_project_id",
        "calendar_events",
        ["project_id"],
    )
    op.create_index(
        "ix_calendar_events_created_by",
        "calendar_events",
        ["created_by"],
    )
    op.create_index(
        "ix_calendar_events_start_at",
        "calendar_events",
        ["start_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_calendar_events_start_at", table_name="calendar_events")
    op.drop_index("ix_calendar_events_created_by", table_name="calendar_events")
    op.drop_index("ix_calendar_events_project_id", table_name="calendar_events")
    op.drop_table("calendar_events")
