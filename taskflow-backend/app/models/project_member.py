"""Associação entre utilizadores e projetos com papéis de acesso limitados."""

from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProjectMember(Base):
    """Membro de projeto; a chave composta impede associações duplicadas."""

    __tablename__ = "project_members"
    __table_args__ = (
        CheckConstraint(
            "role IN ('owner', 'contributor', 'viewer')",
            name="ck_project_members_role",
        ),
    )

    project_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        primary_key=True
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="contributor",
        server_default="contributor",
    )