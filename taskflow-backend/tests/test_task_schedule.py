from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.project import ProjectTaskCreate
from app.schemas.task import TaskCreate, TaskUpdate, validar_periodo_tarefa


def test_task_create_accepts_start_and_due_dates_with_delay_reason() -> None:
    task = TaskCreate(
        project_id=uuid4(),
        title="Preparar lançamento",
        start_date=datetime(2026, 11, 16),
        due_date=datetime(2026, 11, 20),
        delay_reason="  Dependência externa  ",
    )

    assert task.start_date == datetime(2026, 11, 16)
    assert task.due_date == datetime(2026, 11, 20)
    assert task.delay_reason == "Dependência externa"


def test_task_create_rejects_start_date_after_due_date() -> None:
    with pytest.raises(ValidationError, match="data de início não pode ser posterior"):
        TaskCreate(
            project_id=uuid4(),
            title="Preparar lançamento",
            start_date=datetime(2026, 11, 21),
            due_date=datetime(2026, 11, 20),
        )


def test_task_update_allows_partial_dates_and_empty_reason() -> None:
    task_update = TaskUpdate(delay_reason="  ")

    assert task_update.model_dump(exclude_unset=True) == {"delay_reason": None}
    validar_periodo_tarefa(
        datetime(2026, 11, 16),
        datetime(2026, 11, 20),
    )


def test_task_update_rejects_invalid_date_range_when_both_dates_are_sent() -> None:
    with pytest.raises(ValidationError, match="data de início não pode ser posterior"):
        TaskUpdate(
            start_date=datetime(2026, 11, 21),
            due_date=datetime(2026, 11, 20),
        )


def test_initial_project_tasks_accept_schedule_and_delay_reason() -> None:
    task = ProjectTaskCreate(
        title="Preparar lançamento",
        start_date=datetime(2026, 11, 16),
        due_date=datetime(2026, 11, 20),
        delay_reason="Dependência externa",
    )

    assert task.start_date == datetime(2026, 11, 16)
    assert task.due_date == datetime(2026, 11, 20)
    assert task.delay_reason == "Dependência externa"
