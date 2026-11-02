import os
from datetime import datetime, timedelta, timezone
from typing import Generator

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
TOKEN_LIFETIME_MINUTES = 60


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _jwt_secret() -> str:
    secret = os.getenv("TASKFLOW_JWT_SECRET", "")
    if len(secret) < 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Configura TASKFLOW_JWT_SECRET com pelo menos 32 caracteres.",
        )
    return secret


def criar_token_acesso(user: User) -> str:
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
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta área está disponível apenas para administradores.",
        )
    return user
