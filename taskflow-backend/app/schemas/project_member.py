"""Contratos e regras de identificação para membros de projetos."""

from typing import Literal

from pydantic import BaseModel, EmailStr, Field, model_validator


ProjectRole = Literal["owner", "contributor", "viewer"]


class ProjectMemberCreate(BaseModel):
    """Entrada que identifica um único utilizador por ID ou email."""

    user_id: int | None = Field(default=None, gt=0)
    email: EmailStr | None = None
    role: ProjectRole = "contributor"

    @model_validator(mode="after")
    def validar_identificador(self):
        """Exige exatamente um dos identificadores disponíveis."""
        if (self.user_id is None) == (self.email is None):
            raise ValueError("Indica o ID ou o email do utilizador.")
        return self


class ProjectMemberUpdate(BaseModel):
    """Papel definido para uma atualização de membro."""

    role: ProjectRole


class ProjectMemberRoleUpdate(BaseModel):
    """Papel definido pela operação de gestão de membros."""

    role: ProjectRole


class ProjectMemberResponse(BaseModel):
    """Dados de membro devolvidos ao cliente."""

    project_id: int
    user_id: int
    name: str
    email: str
    is_active: bool
    role: ProjectRole
    avatar_url: str | None = None


class ProjectMemberCandidate(BaseModel):
    """Conta elegível apresentada para ser adicionada ao projeto."""

    id: int
    name: str
    email: EmailStr
    avatar_url: str | None = None