"""Modelos de dados para respostas de autenticação."""

from pydantic import BaseModel

from app.schemas.user import UserPublic


class AccessToken(BaseModel):
    """Token bearer devolvido após autenticação bem-sucedida."""

    access_token: str
    token_type: str = "bearer"
