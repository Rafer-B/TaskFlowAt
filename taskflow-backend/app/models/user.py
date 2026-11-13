
"""Modelo de conta, credenciais, papel de acesso e fotografia de perfil."""

from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    JSON,
    String,
    Uuid,
    BigInteger,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    """Utilizador autenticável com estado de atividade e papel na plataforma."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        default=uuid4,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String,
        nullable=False,
        unique=True,
    )
    avatar_url: Mapped[str | None] = mapped_column(
    String(500),
    nullable=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="member",
    )

    session_version: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        server_default="0",
    )

    two_factor_secret: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    two_factor_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    two_factor_last_used_step: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    two_factor_recovery_codes: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default="[]",
    )

    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
