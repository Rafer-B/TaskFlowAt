"""Desafios temporários de autenticação emitidos durante o início de sessão."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TwoFactorLoginChallenge(Base):
    """Regista um desafio assinado e impede que seja reutilizado após o login."""

    __tablename__ = "two_factor_login_challenges"

    challenge_hash: Mapped[str] = mapped_column(String(64), primary_key=True)

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
