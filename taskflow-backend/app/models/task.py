"""Modelo de tarefa com estado, progresso, atribuição e datas de atividade."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    String,
    Text,
    Integer,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Task(Base):
    """Tarefa pertencente a um projeto, com progresso restrito entre 0 e 100."""

    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "progress >= 0 AND progress <= 100",
            name="ck_tasks_progress_range",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )

    project_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("projects.id"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="planning",
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="medium",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="to_do",
    )

    progress: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
    )

    assigned_to: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=True,
    )

    created_by: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )

    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    assignees: Mapped[list["TaskAssignee"]] = relationship(
        "TaskAssignee",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def assignee_ids(self) -> list[int]:
        """Expõe os IDs atribuídos no contrato da API."""
        return [assignee.user_id for assignee in self.assignees]