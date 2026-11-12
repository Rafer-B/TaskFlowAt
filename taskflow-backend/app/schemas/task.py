"""Contratos de tarefas, progresso e registos de trabalho com anexos."""

from datetime import datetime
from typing import Literal
from uuid import UUID

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
    """Dados de criação com valores de estado e prioridade predefinidos."""

    project_id: UUID

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

    assigned_to: UUID | None = None

    assignee_ids: list[UUID] | None = None

    due_date: datetime | None = None

    @field_validator("title")
    @classmethod
    def validar_titulo(cls, valor: str) -> str:
        """Remove espaços periféricos e exige um título não vazio."""
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
        """Normaliza a descrição e converte texto vazio em ausência de valor."""
        if valor is None:
            return None

        valor = valor.strip()

        return valor or None

    @field_validator("assignee_ids")
    @classmethod
    def validar_assignees(
        cls,
        valor: list[UUID] | None,
    ) -> list[UUID] | None:
        """Exige IDs distintos para os membros atribuídos."""
        if valor is None:
            return None
        if len(valor) != len(set(valor)):
            raise ValueError("Não é possível repetir um membro na tarefa.")
        if len(valor) > 1:
            raise ValueError("Uma tarefa só pode ter um responsável.")
        return valor


class TaskUpdate(BaseModel):
    """Campos parciais de edição, com progresso limitado a 0–100."""

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

    progress: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    assigned_to: UUID | None = None

    assignee_ids: list[UUID] | None = None

    due_date: datetime | None = None

    @field_validator("title")
    @classmethod
    def validar_titulo(
        cls,
        valor: str | None,
    ) -> str | None:
        """Normaliza títulos fornecidos sem alterar campos omitidos."""
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
        """Normaliza descrições fornecidas e preserva valores não enviados."""
        if valor is None:
            return None

        valor = valor.strip()

        return valor or None

    @field_validator("assignee_ids")
    @classmethod
    def validar_assignees(
        cls,
        valor: list[UUID] | None,
    ) -> list[UUID] | None:
        """Exige IDs distintos para os membros atribuídos."""
        if valor is None:
            return None
        if len(valor) != len(set(valor)):
            raise ValueError("Não é possível repetir um membro na tarefa.")
        if len(valor) > 1:
            raise ValueError("Uma tarefa só pode ter um responsável.")
        return valor


class TaskResponse(BaseModel):
    """Representação persistida de uma tarefa."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    title: str
    description: str | None
    category: TaskCategory
    priority: TaskPriority
    status: TaskStatus
    progress: int
    assigned_to: UUID | None
    assignee_ids: list[UUID]
    created_by: UUID
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class TaskWorkLogAttachmentResponse(BaseModel):
    """Metadados seguros do anexo, sem expor o caminho armazenado."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_name: str
    content_type: str
    size: int


class TaskWorkLogResponse(BaseModel):
    """Atualização de trabalho com autor e anexos apresentados."""

    id: UUID
    task_id: UUID
    author_id: UUID
    author_name: str
    note: str
    progress: int
    created_at: datetime
    attachments: list[TaskWorkLogAttachmentResponse]