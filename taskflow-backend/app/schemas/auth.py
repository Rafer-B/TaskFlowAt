"""Modelos de dados para respostas de autenticação."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class PasswordResetRequest(BaseModel):
    """Pedido de reposição com token de uso único entregue por um administrador."""

    email: EmailStr
    token: str = Field(min_length=32, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)


class PasswordResetTokenResponse(BaseModel):
    """Token apresentado uma única vez ao administrador emissor."""

    token: str
    expires_at: datetime
