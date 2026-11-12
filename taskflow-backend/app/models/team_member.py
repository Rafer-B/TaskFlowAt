"""Associação de utilizadores a equipas, identificada por uma chave composta."""

from uuid import UUID

from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TeamMember(Base):
    """Par equipa-utilizador cuja chave primária evita membros repetidos."""

    __tablename__ = "team_members"

    team_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
