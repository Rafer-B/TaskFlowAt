"""Impede reutilização de desafios de login com 2FA.

Revision ID: 20261113_0014
Revises: 20261113_0013
Create Date: 2026-11-13
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261113_0014"
down_revision: Union[str, None] = "20261113_0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "two_factor_login_challenges",
        sa.Column("challenge_hash", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("challenge_hash"),
    )
    op.create_index(
        "ix_two_factor_login_challenges_user_id",
        "two_factor_login_challenges",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_two_factor_login_challenges_user_id",
        table_name="two_factor_login_challenges",
    )
    op.drop_table("two_factor_login_challenges")
