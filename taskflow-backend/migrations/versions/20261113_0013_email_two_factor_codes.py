"""Adiciona códigos temporários de 2FA enviados por email.

Revision ID: 20261113_0013
Revises: 20261113_0012
Create Date: 2026-11-13
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261113_0013"
down_revision: Union[str, None] = "20261113_0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "email_login_codes",
        sa.Column("challenge_hash", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "failed_attempts",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("challenge_hash"),
    )
    op.create_index(
        "ix_email_login_codes_user_id",
        "email_login_codes",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_email_login_codes_user_id", table_name="email_login_codes")
    op.drop_table("email_login_codes")
