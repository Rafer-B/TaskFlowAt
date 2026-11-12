"""Converte as chaves primárias e estrangeiras para UUID sem perder dados.

Revision ID: 20261112_0010
Revises: 20261106_0009
Create Date: 2026-11-12
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261112_0010"
down_revision: Union[str, None] = "20261106_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = (
    "users",
    "projects",
    "tasks",
    "project_members",
    "teams",
    "team_members",
    "task_assignees",
    "task_work_logs",
    "task_work_log_attachments",
    "calendar_events",
)

ID_COLUMNS = {
    "users": {"id": ("_uuid_id", False)},
    "projects": {
        "id": ("_uuid_id", False),
        "created_by": ("_uuid_created_by", False),
        "team_id": ("_uuid_team_id", True),
    },
    "tasks": {
        "id": ("_uuid_id", False),
        "project_id": ("_uuid_project_id", False),
        "assigned_to": ("_uuid_assigned_to", True),
        "created_by": ("_uuid_created_by", False),
    },
    "project_members": {
        "project_id": ("_uuid_project_id", False),
        "user_id": ("_uuid_user_id", False),
    },
    "teams": {
        "id": ("_uuid_id", False),
        "created_by": ("_uuid_created_by", False),
    },
    "team_members": {
        "team_id": ("_uuid_team_id", False),
        "user_id": ("_uuid_user_id", False),
    },
    "task_assignees": {
        "task_id": ("_uuid_task_id", False),
        "user_id": ("_uuid_user_id", False),
    },
    "task_work_logs": {
        "id": ("_uuid_id", False),
        "task_id": ("_uuid_task_id", False),
        "author_id": ("_uuid_author_id", False),
    },
    "task_work_log_attachments": {
        "id": ("_uuid_id", False),
        "work_log_id": ("_uuid_work_log_id", False),
    },
    "calendar_events": {
        "id": ("_uuid_id", False),
        "project_id": ("_uuid_project_id", True),
        "created_by": ("_uuid_created_by", False),
    },
}

PRIMARY_KEYS = {
    "users": ["id"],
    "projects": ["id"],
    "tasks": ["id"],
    "project_members": ["project_id", "user_id"],
    "teams": ["id"],
    "team_members": ["team_id", "user_id"],
    "task_assignees": ["task_id", "user_id"],
    "task_work_logs": ["id"],
    "task_work_log_attachments": ["id"],
    "calendar_events": ["id"],
}

FOREIGN_KEYS = (
    ("projects", "created_by", "users", "id", None),
    ("projects", "team_id", "teams", "id", "SET NULL"),
    ("tasks", "project_id", "projects", "id", None),
    ("tasks", "assigned_to", "users", "id", None),
    ("tasks", "created_by", "users", "id", None),
    ("project_members", "project_id", "projects", "id", "CASCADE"),
    ("project_members", "user_id", "users", "id", "CASCADE"),
    ("teams", "created_by", "users", "id", None),
    ("team_members", "team_id", "teams", "id", "CASCADE"),
    ("team_members", "user_id", "users", "id", "CASCADE"),
    ("task_assignees", "task_id", "tasks", "id", "CASCADE"),
    ("task_assignees", "user_id", "users", "id", "CASCADE"),
    ("task_work_logs", "task_id", "tasks", "id", "CASCADE"),
    ("task_work_logs", "author_id", "users", "id", None),
    (
        "task_work_log_attachments",
        "work_log_id",
        "task_work_logs",
        "id",
        "CASCADE",
    ),
    ("calendar_events", "project_id", "projects", "id", "CASCADE"),
    ("calendar_events", "created_by", "users", "id", None),
)


def _drop_key_constraints() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    foreign_keys = {
        table: inspector.get_foreign_keys(table)
        for table in TABLES
    }
    unique_constraints = {
        table: inspector.get_unique_constraints(table)
        for table in TABLES
    }
    primary_keys = {
        table: inspector.get_pk_constraint(table)
        for table in TABLES
    }

    for table in TABLES:
        for foreign_key in foreign_keys[table]:
            if foreign_key["name"]:
                op.drop_constraint(
                    foreign_key["name"],
                    table,
                    type_="foreignkey",
                )

    for table in TABLES:
        for unique in unique_constraints[table]:
            if unique["name"] and set(unique["column_names"]) & set(
                ID_COLUMNS[table]
            ):
                op.drop_constraint(unique["name"], table, type_="unique")

    for table in TABLES:
        primary_key = primary_keys[table]
        if primary_key["name"]:
            op.drop_constraint(
                primary_key["name"],
                table,
                type_="primary",
            )


def _create_key_constraints() -> None:
    for table, columns in PRIMARY_KEYS.items():
        op.create_primary_key(f"pk_{table}", table, columns)

    for table, column, referenced_table, referenced_column, ondelete in (
        FOREIGN_KEYS
    ):
        op.create_foreign_key(
            f"fk_{table}_{column}_{referenced_table}",
            table,
            referenced_table,
            [column],
            [referenced_column],
            ondelete=ondelete,
        )

    op.create_unique_constraint(
        "uq_task_assignees_task_id",
        "task_assignees",
        ["task_id"],
    )


def upgrade() -> None:
    """Gera UUIDs novos e remapeia as referências existentes."""
    for table, columns in ID_COLUMNS.items():
        for _, (new_column, _) in columns.items():
            op.add_column(table, sa.Column(new_column, sa.Uuid(), nullable=True))

    for table, columns in PRIMARY_KEYS.items():
        if columns == ["id"]:
            op.execute(
                sa.text(
                    f"UPDATE {table} SET _uuid_id = gen_random_uuid()"
                )
            )

    for table, column, referenced_table, referenced_column, _ in FOREIGN_KEYS:
        new_column = ID_COLUMNS[table][column][0]
        referenced_new_column = ID_COLUMNS[referenced_table][referenced_column][0]
        op.execute(
            sa.text(
                f"UPDATE {table} AS source "
                f"SET {new_column} = target.{referenced_new_column} "
                f"FROM {referenced_table} AS target "
                f"WHERE source.{column} = target.{referenced_column}"
            )
        )

    _drop_key_constraints()

    for table, columns in ID_COLUMNS.items():
        for column, (new_column, nullable) in columns.items():
            op.drop_column(table, column)
            op.alter_column(
                table,
                new_column,
                new_column_name=column,
                existing_type=sa.Uuid(),
                nullable=nullable,
            )

    _create_key_constraints()

    op.create_index("ix_projects_team_id", "projects", ["team_id"])
    op.create_index(
        "ix_task_work_logs_task_id",
        "task_work_logs",
        ["task_id"],
    )
    op.create_index(
        "ix_task_work_log_attachments_work_log_id",
        "task_work_log_attachments",
        ["work_log_id"],
    )
    op.create_index(
        "ix_calendar_events_project_id",
        "calendar_events",
        ["project_id"],
    )
    op.create_index(
        "ix_calendar_events_created_by",
        "calendar_events",
        ["created_by"],
    )


def downgrade() -> None:
    """Restaura chaves inteiras novas, preservando as relações e os registos."""
    integer_types = {
        ("task_work_logs", "id"): sa.Integer(),
        ("task_work_log_attachments", "id"): sa.Integer(),
        ("task_work_log_attachments", "work_log_id"): sa.Integer(),
    }

    for table, columns in ID_COLUMNS.items():
        for column, (new_column, _) in columns.items():
            column_type = integer_types.get((table, column), sa.BigInteger())
            identity = (
                sa.Identity(always=True)
                if column == "id" and PRIMARY_KEYS[table] == ["id"]
                else None
            )
            op.add_column(
                table,
                sa.Column(
                    new_column,
                    column_type,
                    identity=identity,
                    nullable=True,
                ),
            )

    for table, column, referenced_table, referenced_column, _ in FOREIGN_KEYS:
        new_column = ID_COLUMNS[table][column][0]
        referenced_new_column = ID_COLUMNS[referenced_table][referenced_column][0]
        op.execute(
            sa.text(
                f"UPDATE {table} AS source "
                f"SET {new_column} = target.{referenced_new_column} "
                f"FROM {referenced_table} AS target "
                f"WHERE source.{column} = target.{referenced_column}"
            )
        )

    _drop_key_constraints()

    for table, columns in ID_COLUMNS.items():
        for column, (new_column, nullable) in columns.items():
            op.drop_column(table, column)
            op.alter_column(
                table,
                new_column,
                new_column_name=column,
                existing_type=integer_types.get(
                    (table, column),
                    sa.BigInteger(),
                ),
                nullable=nullable,
            )

    _create_key_constraints()

    op.create_index("ix_projects_team_id", "projects", ["team_id"])
    op.create_index(
        "ix_task_work_logs_task_id",
        "task_work_logs",
        ["task_id"],
    )
    op.create_index(
        "ix_task_work_log_attachments_work_log_id",
        "task_work_log_attachments",
        ["work_log_id"],
    )
    op.create_index(
        "ix_calendar_events_project_id",
        "calendar_events",
        ["project_id"],
    )
    op.create_index(
        "ix_calendar_events_created_by",
        "calendar_events",
        ["created_by"],
    )
