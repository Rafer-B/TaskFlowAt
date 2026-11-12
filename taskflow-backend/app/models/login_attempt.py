"""Contador persistente para limitar tentativas de autenticação."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LoginAttempt(Base):
    """Janela de tentativas indexada por fingerprint não reversível."""

    __tablename__ = "login_attempts"

    fingerprint: Mapped[str] = mapped_column(String(64), primary_key=True)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    window_started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    blocked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
