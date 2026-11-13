"""Dependências de autenticação, sessão da base de dados e permissões."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Generator
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.project_member import ProjectMember
from app.models.two_factor_login_challenge import TwoFactorLoginChallenge
from app.models.user import User
from app.settings import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """Fornece uma sessão por pedido e fecha-a mesmo quando ocorre um erro."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _jwt_secret() -> str:
    """Obtém a chave JWT e impede o serviço de operar com uma chave fraca."""
    secret = settings.jwt_secret
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
            "exp": agora + timedelta(minutes=settings.session_lifetime_minutes),
            "ver": user.session_version,
        },
        _jwt_secret(),
        algorithm="HS256",
    )


def criar_token_desafio_2fa(user: User) -> str:
    """Assina um token de curta duração que só permite concluir o login 2FA."""
    agora = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(user.id),
            "iat": agora,
            "exp": agora + timedelta(minutes=5),
            "ver": user.session_version,
            "purpose": "2fa-login",
            "jti": secrets.token_urlsafe(16),
        },
        _jwt_secret(),
        algorithm="HS256",
    )


def obter_utilizador_desafio_2fa(token: str, db: Session) -> User:
    """Valida o desafio de login e devolve uma conta ainda ativa e não revogada."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Desafio de autenticação inválido ou expirado.",
    )

    try:
        payload = jwt.decode(
            token,
            _jwt_secret(),
            algorithms=["HS256"],
            options={"require": ["sub", "exp", "ver", "purpose", "jti"]},
        )
        if payload["purpose"] != "2fa-login":
            raise ValueError("Invalid challenge purpose")
        user_id = UUID(payload["sub"])
        token_version = payload["ver"]
        if not isinstance(token_version, int):
            raise ValueError("Invalid token version")
    except (InvalidTokenError, KeyError, TypeError, ValueError):
        raise unauthorized

    now = datetime.now(timezone.utc)
    challenge_hash = hashlib.sha256(token.encode()).hexdigest()
    challenge = db.scalar(
        select(TwoFactorLoginChallenge)
        .where(TwoFactorLoginChallenge.challenge_hash == challenge_hash)
        .with_for_update()
    )
    if (
        challenge is None
        or challenge.consumed_at is not None
        or _challenge_expired(challenge.expires_at, now)
        or challenge.user_id != user_id
    ):
        raise unauthorized

    user = db.scalar(
        select(User).where(User.id == user_id).with_for_update()
    )
    if (
        user is None
        or not user.is_active
        or user.session_version != token_version
        or not user.two_factor_enabled
    ):
        raise unauthorized

    return user


def _challenge_expired(expires_at: datetime, now: datetime) -> bool:
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at <= now


def obter_utilizador_atual(
    request: Request,
    bearer_token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Valida o token e exige que a conta correspondente continue ativa."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sessão inválida ou expirada.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    cookie_token = request.cookies.get(settings.session_cookie_name)
    token = bearer_token or cookie_token
    if not token:
        raise unauthorized

    if cookie_token and bearer_token is None and request.method not in {
        "GET",
        "HEAD",
        "OPTIONS",
    }:
        csrf_cookie = request.cookies.get(settings.csrf_cookie_name, "")
        csrf_header = request.headers.get("x-csrf-token", "")
        if (
            not csrf_cookie
            or not csrf_header
            or not secrets.compare_digest(csrf_cookie, csrf_header)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token CSRF inválido.",
            )

    try:
        payload = jwt.decode(
            token,
            _jwt_secret(),
            algorithms=["HS256"],
            options={"require": ["sub", "exp"]},
        )
        user_id = UUID(payload["sub"])
        token_version = payload["ver"]
        if not isinstance(token_version, int):
            raise ValueError("Invalid token version")
    except (InvalidTokenError, KeyError, TypeError, ValueError):
        raise unauthorized

    user = db.get(User, user_id)
    if (
        user is None
        or not user.is_active
        or user.session_version != token_version
    ):
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
    project_id: UUID,
    user: User,
) -> str | None:
    """Devolve o papel no projeto; administradores têm acesso transversal."""
    if user.role == "admin":
        return "admin"

    membership = db.get(ProjectMember, (project_id, user.id))
    return membership.role if membership is not None else None


def exigir_papel_projeto(
    db: Session,
    project_id: UUID,
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
