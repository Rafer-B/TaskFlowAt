from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import User


class TaskWorkLog(Base):
    __tablename__ = "task_work_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        Identity(always=True),
        primary_key=True,
    )

    task_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    author_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )

    note: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    progress: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    author: Mapped[User] = relationship()
    attachments: Mapped[list["TaskWorkLogAttachment"]] = relationship(
        back_populates="work_log",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class TaskWorkLogAttachment(Base):
    __tablename__ = "task_work_log_attachments"

    id: Mapped[int] = mapped_column(
        Integer,
        Identity(always=True),
        primary_key=True,
    )

    work_log_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("task_work_logs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    original_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    stored_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        unique=True,
    )

    content_type: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    work_log: Mapped[TaskWorkLog] = relationship(
        back_populates="attachments",
    )
