"""Associação entre tarefas e os membros responsáveis por as executar."""

from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TaskAssignee(Base):
    """Associa uma tarefa ao seu único membro responsável."""

    __tablename__ = "task_assignees"
    __table_args__ = (
        UniqueConstraint("task_id", name="uq_task_assignees_task_id"),
    )

    task_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        primary_key=True,
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
