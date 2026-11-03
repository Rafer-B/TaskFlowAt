
"""Contratos de validação e resposta para operações de projetos."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ProjectStatus = Literal["active", "completed", "archived"]


class ProjectCreate(BaseModel):
    """Campos aceites para criar um projeto."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


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
