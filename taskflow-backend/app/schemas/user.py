
"""Contratos de entrada e saída para contas e perfis de utilizador."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

UserRole = Literal["admin", "member"]


class UserCreate(BaseModel):
    """Dados para criar uma conta com palavra-passe e papel inicial."""

    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = "member"


class UserRoleUpdate(BaseModel):
    """Novo papel de acesso definido por um administrador."""

    role: UserRole


class UserUpdate(BaseModel):
    """Campos editáveis de perfil, com normalização do nome."""

    name: str | None = Field(default=None, min_length=2, max_length=100)
    email: EmailStr | None = None

    @field_validator("name")
    @classmethod
    def validar_nome(cls, valor: str | None) -> str | None:
        """Permite campos omitidos, mas exige dois caracteres após normalizar."""
        if valor is None:
            return None

        valor = valor.strip()
        if len(valor) < 2:
            raise ValueError("O nome deve ter pelo menos 2 caracteres.")
        return valor


class UserPasswordUpdate(BaseModel):
    """Palavra-passe atual e nova para alteração autenticada."""

    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class UserPublic(BaseModel):
    """Campos de conta expostos, sem credenciais ou hash da palavra-passe."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: UserRole
    avatar_url: str | None = None
    is_active: bool
    created_at: datetime
