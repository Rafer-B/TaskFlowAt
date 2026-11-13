"""Modelos de dados para respostas de autenticação."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class TwoFactorChallenge(BaseModel):
    """Desafio temporário emitido após credenciais válidas para contas com 2FA."""

    requires_two_factor: Literal[True] = True
    challenge_token: str
    methods: list[Literal["authenticator", "email"]]


class TwoFactorLoginRequest(BaseModel):
    """Código TOTP ou de recuperação para concluir o início de sessão."""

    challenge_token: str = Field(min_length=32, max_length=2048)
    code: str = Field(min_length=6, max_length=32)


class TwoFactorEmailRequest(BaseModel):
    """Desafio de login para enviar um código ao endereço da conta."""

    challenge_token: str = Field(min_length=32, max_length=2048)


class TwoFactorSetupRequest(BaseModel):
    """Confirma a palavra-passe antes de iniciar a configuração do autenticador."""

    current_password: str = Field(min_length=1, max_length=128)


class TwoFactorCodeRequest(BaseModel):
    """Código TOTP para ativar o segundo fator."""

    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class TwoFactorDisableRequest(BaseModel):
    """Credenciais necessárias para desativar a autenticação de dois fatores."""

    current_password: str = Field(min_length=1, max_length=128)
    code: str = Field(min_length=6, max_length=32)


class PasswordResetRequest(BaseModel):
    """Pedido de reposição com token de uso único entregue por um administrador."""

    email: EmailStr
    token: str = Field(min_length=32, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)


class PasswordResetTokenResponse(BaseModel):
    """Token apresentado uma única vez ao administrador emissor."""

    token: str
    expires_at: datetime
