"""Rotas para autenticar contas e consultar a identidade da sessão atual."""

from datetime import datetime, timedelta, timezone
import hashlib
import hmac

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.auth import get_db, obter_utilizador_atual
from app.models.login_attempt import LoginAttempt
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.schemas.auth import PasswordResetRequest
from app.schemas.user import UserPublic
from app.sessions import clear_session_cookies, set_session_cookies
from app.settings import settings

router = APIRouter(prefix="/auth", tags=["Autenticação"])
password_hash = PasswordHash.recommended()
DUMMY_PASSWORD_HASH = password_hash.hash("not-a-real-user-password")
MAX_LOGIN_FAILURES = 5
LOGIN_WINDOW = timedelta(minutes=15)
LOGIN_BLOCK_DURATION = timedelta(minutes=15)


def _login_fingerprints(email: str, remote_host: str) -> tuple[str, str]:
    secret = settings.jwt_secret or "development-only-login-rate-limit-key"
    values = (f"account:{email}:{remote_host}", f"ip:{remote_host}")
    return tuple(
        hmac.new(secret.encode(), value.encode(), hashlib.sha256).hexdigest()
        for value in values
    )


def _is_login_blocked(db: Session, fingerprints: tuple[str, str]) -> bool:
    now = datetime.now(timezone.utc)
    return db.scalar(
        select(LoginAttempt.fingerprint)
        .where(
            LoginAttempt.fingerprint.in_(fingerprints),
            LoginAttempt.blocked_until > now,
        )
        .limit(1)
    ) is not None


def _record_login_failure(
    db: Session,
    fingerprints: tuple[str, str],
) -> None:
    now = datetime.now(timezone.utc)
    for fingerprint in fingerprints:
        statement = insert(LoginAttempt).values(
            fingerprint=fingerprint,
            failed_count=1,
            window_started_at=now,
            blocked_until=None,
        )
        expired_window = LoginAttempt.window_started_at <= now - LOGIN_WINDOW
        count = (
            1
            if expired_window
            else LoginAttempt.failed_count + 1
        )
        statement = statement.on_conflict_do_update(
            index_elements=[LoginAttempt.fingerprint],
            set_={
                "failed_count": count,
                "window_started_at": (
                    now if expired_window else LoginAttempt.window_started_at
                ),
                "blocked_until": (
                    now + LOGIN_BLOCK_DURATION
                    if count >= MAX_LOGIN_FAILURES
                    else None
                ),
            },
        )
        db.execute(statement)
    db.commit()


def _clear_login_failures(
    db: Session,
    fingerprints: tuple[str, str],
) -> None:
    db.execute(
        delete(LoginAttempt).where(
            LoginAttempt.fingerprint.in_(fingerprints),
        )
    )


@router.post("/login", response_model=UserPublic)
def login(
    request: Request,
    response: Response,
    dados: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> UserPublic:
    """Valida credenciais e emite um token sem revelar se o email existe."""
    email = dados.username.strip().lower()
    remote_host = request.client.host if request and request.client else "unknown"
    fingerprints = _login_fingerprints(email, remote_host)
    if _is_login_blocked(db, fingerprints):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas de acesso. Tente novamente em 15 minutos.",
            headers={"Retry-After": str(int(LOGIN_BLOCK_DURATION.total_seconds()))},
        )

    user = db.scalar(select(User).where(User.email == email))

    # O hash fictício mantém uma verificação de custo semelhante para emails inexistentes.
    hash_para_verificar = (
        user.password_hash if user is not None else DUMMY_PASSWORD_HASH
    )
    palavra_passe_valida = password_hash.verify(
        dados.password,
        hash_para_verificar,
    )

    if user is None or not user.is_active or not palavra_passe_valida:
        _record_login_failure(db, fingerprints)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou palavra-passe inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    _clear_login_failures(db, fingerprints)
    db.commit()
    set_session_cookies(response, user)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
) -> Response:
    user.session_version += 1
    db.commit()
    clear_session_cookies(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post("/password-reset", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(
    dados: PasswordResetRequest,
    db: Session = Depends(get_db),
) -> None:
    """Consome um token administrativo de uso único sem revelar contas."""
    email = str(dados.email).strip().lower()
    token_hash = hashlib.sha256(dados.token.encode()).hexdigest()
    now = datetime.now(timezone.utc)
    reset_token = db.scalar(
        select(PasswordResetToken)
        .join(User, User.id == PasswordResetToken.user_id)
        .where(
            User.email == email,
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
        .with_for_update()
    )
    if reset_token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Os dados de recuperação são inválidos ou expiraram.",
        )

    user = db.get(User, reset_token.user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Os dados de recuperação são inválidos ou expiraram.",
        )
    reset_token.used_at = now
    user.password_hash = password_hash.hash(dados.new_password)
    user.session_version += 1
    db.commit()


@router.get("/me", response_model=UserPublic)
def utilizador_atual(
    user: User = Depends(obter_utilizador_atual),
) -> User:
    """Devolve o utilizador autenticado associado ao token enviado."""
    return user
