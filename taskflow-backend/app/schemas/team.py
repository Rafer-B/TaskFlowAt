"""Contratos de equipas, associação de membros e projetos."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TeamCreate(BaseModel):
    """Entrada de criação com normalização de nome e descrição."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def validar_nome(self):
        """Remove espaços e exige um nome que não fique vazio."""
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("O nome da equipa é obrigatório.")
        if self.description is not None:
            self.description = self.description.strip() or None
        return self


class TeamUpdate(BaseModel):
    """Campos opcionais de equipa, validando nulos explicitamente enviados."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def validar_campos(self):
        """Distingue omissão de null e normaliza os textos alterados."""
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("O nome da equipa é obrigatório.")
        if self.name is not None:
            self.name = self.name.strip()
            if not self.name:
                raise ValueError("O nome da equipa é obrigatório.")
        if self.description is not None:
            self.description = self.description.strip() or None
        return self


class TeamProjectResponse(BaseModel):
    """Resumo de um projeto associado à equipa."""

    id: UUID
    name: str
    status: str


class TeamResponse(BaseModel):
    """Dados da equipa e permissões disponíveis para o utilizador."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    member_count: int
    projects: list[TeamProjectResponse]
    can_manage: bool
    can_associate_projects: bool


class TeamMemberCreate(BaseModel):
    """Identificador da conta a adicionar à equipa."""

    user_id: UUID


class TeamMembersCreate(BaseModel):
    """Lista limitada e sem duplicados de contas a adicionar em lote."""

    user_ids: list[UUID] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validar_ids_unicos(self):
        """Exige IDs distintos antes de iniciar a operação em lote."""
        if len(set(self.user_ids)) != len(self.user_ids):
            raise ValueError("A lista contém utilizadores repetidos.")
        return self


class TeamMemberResponse(BaseModel):
    """Dados públicos de um membro de equipa."""

    user_id: UUID
    name: str
    email: str
    avatar_url: str | None = None


class TeamMemberCandidate(TeamMemberResponse):
    """Membro elegível apresentado para seleção."""

    pass
