"""Associação entre tarefas e os membros responsáveis por as executar."""

from sqlalchemy import BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TaskAssignee(Base):
    """Associa uma tarefa ao seu único membro responsável."""

    __tablename__ = "task_assignees"
    __table_args__ = (
        UniqueConstraint("task_id", name="uq_task_assignees_task_id"),
    )

    task_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
