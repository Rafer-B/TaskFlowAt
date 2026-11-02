"""Create workspace teams and project associations.

Revision ID: 20261102_0007
Revises: 20261102_0006
Create Date: 2026-11-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261102_0007"
down_revision: Union[str, None] = "20261102_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "teams",
        sa.Column(
            "id",
            sa.BigInteger(),
            sa.Identity(always=True),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "team_members",
        sa.Column("team_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["team_id"],
            ["teams.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("team_id", "user_id"),
    )
    op.add_column(
        "projects",
        sa.Column("team_id", sa.BigInteger(), nullable=True),
    )
    op.create_foreign_key(
        "fk_projects_team_id_teams",
        "projects",
        "teams",
        ["team_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_projects_team_id", "projects", ["team_id"])


def downgrade() -> None:
    op.drop_index("ix_projects_team_id", table_name="projects")
    op.drop_constraint(
        "fk_projects_team_id_teams",
        "projects",
        type_="foreignkey",
    )
    op.drop_column("projects", "team_id")
    op.drop_table("team_members")
    op.drop_table("teams")
