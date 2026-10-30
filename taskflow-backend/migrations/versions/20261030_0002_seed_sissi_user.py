"""Create the requested initial user.

Revision ID: 20261030_0002
Revises: 20261030_0001
Create Date: 2026-10-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261030_0002"
down_revision: Union[str, None] = "20261030_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO users (name, email, password_hash)
            VALUES (:name, :email, :password_hash)
            ON CONFLICT (email) DO NOTHING
            """
        ).bindparams(
            name="Utilizador",
            email="sissi@gmail.com",
            password_hash=(
                "$argon2id$v=19$m=65536,t=3,p=4$UWxeyOzC5RzMOo+WSGLw5g"
                "$B5Q1eyrti+1ZnPxLIWgvAyXkoa59sQbz2Z/Cyc9oWpE"
            ),
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM users WHERE email = :email").bindparams(
            email="sissi@gmail.com"
        )
    )
