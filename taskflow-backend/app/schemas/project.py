
"""Contratos de validação e resposta para operações de projetos."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


ProjectStatus = Literal["active", "completed", "archived"]


class ProjectTaskCreate(BaseModel):
    """Tarefa inicial associada atomicamente ao novo projeto."""

    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)

    @field_validator("title")
    @classmethod
    def validar_titulo(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("O título da tarefa é obrigatório.")
        return valor

    @field_validator("description")
    @classmethod
    def validar_descricao(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        return valor.strip() or None


class ProjectCreate(BaseModel):
    """Campos e associações aceites ao criar um projeto."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    team_id: int | None = Field(default=None, gt=0)
    member_ids: list[int] = Field(default_factory=list, max_length=100)
    tasks: list[ProjectTaskCreate] = Field(default_factory=list, max_length=100)

    @field_validator("name")
    @classmethod
    def validar_nome(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("O nome do projeto é obrigatório.")
        return valor

    @model_validator(mode="after")
    def validar_associacoes(self):
        if any(user_id <= 0 for user_id in self.member_ids):
            raise ValueError("Os IDs dos membros devem ser positivos.")
        if len(set(self.member_ids)) != len(self.member_ids):
            raise ValueError("A lista contém membros repetidos.")
        return self


class ProjectUpdate(BaseModel):
    """Campos opcionais alteráveis num projeto existente."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: ProjectStatus | None = None


class ProjectResponse(BaseModel):
    """Dados de projeto, incluindo o papel do utilizador atual quando conhecido."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    status: str
    created_by: int
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    team_id: int | None = None
    current_user_role: Literal[
        "admin",
        "owner",
        "contributor",
        "viewer",
    ] | None = None
