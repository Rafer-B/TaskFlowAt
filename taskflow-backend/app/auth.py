"""Dependências de autenticação, sessão da base de dados e permissões."""

import os
from datetime import datetime, timedelta, timezone
from typing import Generator

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.project_member import ProjectMember
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
TOKEN_LIFETIME_MINUTES = 60


def get_db() -> Generator[Session, None, None]:
    """Fornece uma sessão por pedido e fecha-a mesmo quando ocorre um erro."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _jwt_secret() -> str:
    """Obtém a chave JWT e impede o serviço de operar com uma chave fraca."""
    secret = os.getenv("TASKFLOW_JWT_SECRET", "")
    if len(secret) < 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Configura TASKFLOW_JWT_SECRET com pelo menos 32 caracteres.",
        )
    return secret


def criar_token_acesso(user: User) -> str:
    """Assina um token de acesso com identificador, emissão e validade."""
    agora = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(user.id),
            "iat": agora,
            "exp": agora + timedelta(minutes=TOKEN_LIFETIME_MINUTES),
        },
        _jwt_secret(),
        algorithm="HS256",
    )


def obter_utilizador_atual(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Valida o token e exige que a conta correspondente continue ativa."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sessão inválida ou expirada.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            _jwt_secret(),
            algorithms=["HS256"],
            options={"require": ["sub", "exp"]},
        )
        user_id = int(payload["sub"])
    except (InvalidTokenError, TypeError, ValueError):
        raise unauthorized

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise unauthorized

    return user


def exigir_administrador(
    user: User = Depends(obter_utilizador_atual),
) -> User:
    """Restringe a operação a utilizadores com o papel de administrador."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta área está disponível apenas para administradores.",
        )
    return user


def obter_papel_projeto(
    db: Session,
    project_id: int,
    user: User,
) -> str | None:
    """Devolve o papel no projeto; administradores têm acesso transversal."""
    if user.role == "admin":
        return "admin"

    membership = db.get(ProjectMember, (project_id, user.id))
    return membership.role if membership is not None else None


def exigir_papel_projeto(
    db: Session,
    project_id: int,
    user: User,
    papeis_permitidos: set[str] | None = None,
) -> str:
    """Exige associação ao projeto e, se indicado, um dos papéis permitidos."""
    role = obter_papel_projeto(db, project_id, user)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projeto não encontrado.",
        )
    if papeis_permitidos is not None and role not in papeis_permitidos:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não tem permissões suficientes para este projeto.",
        )
    return role
