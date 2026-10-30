from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


TaskCategory = Literal[
    "planning",
    "research",
    "design",
    "development",
    "validation",
    "documentation",
]

TaskPriority = Literal[
    "low",
    "medium",
    "high",
]

TaskStatus = Literal[
    "to_do",
    "in_progress",
    "completed",
    "blocked",
]


class TaskCreate(BaseModel):
    project_id: int = Field(gt=0)

    title: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    category: TaskCategory = "planning"

    priority: TaskPriority = "medium"

    status: TaskStatus = "to_do"

    assigned_to: int | None = Field(
        default=None,
        gt=0,
    )

    created_by: int = Field(gt=0)

    due_date: datetime | None = None

    @field_validator("title")
    @classmethod
    def validar_titulo(cls, valor: str) -> str:
        valor = valor.strip()

        if not valor:
            raise ValueError("O título da tarefa é obrigatório.")

        return valor

    @field_validator("description")
    @classmethod
    def validar_descricao(
        cls,
        valor: str | None,
    ) -> str | None:
        if valor is None:
            return None

        valor = valor.strip()

        return valor or None


class TaskUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    category: TaskCategory | None = None

    priority: TaskPriority | None = None

    status: TaskStatus | None = None

    assigned_to: int | None = Field(
        default=None,
        gt=0,
    )

    due_date: datetime | None = None

    @field_validator("title")
    @classmethod
    def validar_titulo(
        cls,
        valor: str | None,
    ) -> str | None:
        if valor is None:
            return None

        valor = valor.strip()

        if not valor:
            raise ValueError("O título da tarefa é obrigatório.")

        return valor

    @field_validator("description")
    @classmethod
    def validar_descricao(
        cls,
        valor: str | None,
    ) -> str | None:
        if valor is None:
            return None

        valor = valor.strip()

        return valor or None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    title: str
    description: str | None
    category: TaskCategory
    priority: TaskPriority
    status: TaskStatus
    assigned_to: int | None
    created_by: int
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None