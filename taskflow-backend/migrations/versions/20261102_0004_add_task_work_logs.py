"""Adiciona progresso a tarefas e tabelas de registos de trabalho e anexos.

Revision ID: 20261102_0004
Revises: 20261102_0003
Create Date: 2026-11-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261102_0004"
down_revision: Union[str, None] = "20261102_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria limites de progresso e estrutura de registos com os seus ficheiros."""
    op.add_column(
        "tasks",
        sa.Column(
            "progress",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_tasks_progress_range",
        "tasks",
        "progress >= 0 AND progress <= 100",
    )
    # Normaliza tarefas já concluídas para satisfazer a nova regra de progresso.
    op.execute(
        sa.text(
            "UPDATE tasks SET progress = 100 WHERE status = 'completed'"
        )
    )

    op.create_table(
        "task_work_logs",
        sa.Column(
            "id",
            sa.Integer(),
            sa.Identity(always=True),
            nullable=False,
        ),
        sa.Column("task_id", sa.BigInteger(), nullable=False),
        sa.Column("author_id", sa.BigInteger(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "progress >= 0 AND progress <= 100",
            name="ck_task_work_logs_progress_range",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_task_work_logs_task_id",
        "task_work_logs",
        ["task_id"],
    )

    op.create_table(
        "task_work_log_attachments",
        sa.Column(
            "id",
            sa.Integer(),
            sa.Identity(always=True),
            nullable=False,
        ),
        sa.Column("work_log_id", sa.Integer(), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column(
            "stored_path",
            sa.String(length=500),
            nullable=False,
        ),
        sa.Column("content_type", sa.String(length=150), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["work_log_id"],
            ["task_work_logs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stored_path"),
    )
    op.create_index(
        "ix_task_work_log_attachments_work_log_id",
        "task_work_log_attachments",
        ["work_log_id"],
    )


def downgrade() -> None:
    """Remove anexos e registos antes de retirar o progresso das tarefas."""
    op.drop_index(
        "ix_task_work_log_attachments_work_log_id",
        table_name="task_work_log_attachments",
    )
    op.drop_table("task_work_log_attachments")
    op.drop_index(
        "ix_task_work_logs_task_id",
        table_name="task_work_logs",
    )
    op.drop_table("task_work_logs")
    op.drop_constraint(
        "ck_tasks_progress_range",
        "tasks",
        type_="check",
    )
    op.drop_column("tasks", "progress")
