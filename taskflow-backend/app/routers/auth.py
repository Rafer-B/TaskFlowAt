"""Rotas para autenticar contas e consultar a identidade da sessão atual."""

from datetime import datetime, timedelta, timezone
import base64
from io import BytesIO
import hashlib
import hmac
import json
import logging
import secrets
from urllib.error import HTTPError, URLError
from urllib.request import Request as URLRequest, urlopen

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
import pyotp
from pwdlib import PasswordHash
import qrcode
from qrcode.image.svg import SvgPathImage
from sqlalchemy import case, delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.auth import (
    criar_token_desafio_2fa,
    get_db,
    obter_utilizador_atual,
    obter_utilizador_desafio_2fa,
)
from app.models.login_attempt import LoginAttempt
from app.models.email_login_code import EmailLoginCode
from app.models.password_reset_token import PasswordResetToken
from app.models.two_factor_login_challenge import TwoFactorLoginChallenge
from app.models.user import User
from app.schemas.auth import (
    PasswordResetRequest,
    TwoFactorChallenge,
    TwoFactorCodeRequest,
    TwoFactorDisableRequest,
    TwoFactorEmailRequest,
    TwoFactorLoginRequest,
    TwoFactorSetupRequest,
)
from app.schemas.user import UserPublic
from app.sessions import clear_session_cookies, set_session_cookies
from app.settings import settings

router = APIRouter(prefix="/auth", tags=["Autenticação"])
password_hash = PasswordHash.recommended()
DUMMY_PASSWORD_HASH = password_hash.hash("not-a-real-user-password")
MAX_LOGIN_FAILURES = 5
LOGIN_WINDOW = timedelta(minutes=15)
LOGIN_BLOCK_DURATION = timedelta(minutes=15)
RECOVERY_CODE_COUNT = 10
EMAIL_CODE_TTL = timedelta(minutes=5)
EMAIL_CODE_RESEND_DELAY = timedelta(seconds=60)
MAX_EMAIL_CODE_FAILURES = 5
logger = logging.getLogger(__name__)


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
        count = case(
            (expired_window, 1),
            else_=LoginAttempt.failed_count + 1,
        )
        statement = statement.on_conflict_do_update(
            index_elements=[LoginAttempt.fingerprint],
            set_={
                "failed_count": count,
                "window_started_at": case(
                    (expired_window, now),
                    else_=LoginAttempt.window_started_at,
                ),
                "blocked_until": case(
                    (count >= MAX_LOGIN_FAILURES, now + LOGIN_BLOCK_DURATION),
                    else_=None,
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


def _fernet_key() -> bytes:
    secret = settings.jwt_secret
    if len(secret) < 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="A autenticação de dois fatores não está configurada.",
        )
    key = hmac.new(
        secret.encode(),
        b"taskflow-two-factor-encryption",
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(key)


def _encrypt_two_factor_secret(secret: str) -> str:
    from cryptography.fernet import Fernet

    return Fernet(_fernet_key()).encrypt(secret.encode()).decode()


def _decrypt_two_factor_secret(encrypted_secret: str) -> str:
    from cryptography.fernet import Fernet, InvalidToken

    try:
        return Fernet(_fernet_key()).decrypt(encrypted_secret.encode()).decode()
    except InvalidToken as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível validar o autenticador. Contacte o suporte.",
        ) from error


def _recovery_code_hash(code: str) -> str:
    return hmac.new(
        settings.jwt_secret.encode(),
        f"taskflow-two-factor-recovery:{code}".encode(),
        hashlib.sha256,
    ).hexdigest()


def _validar_codigo_totp(user: User, code: str) -> bool:
    if not user.two_factor_secret:
        return False

    totp = pyotp.TOTP(_decrypt_two_factor_secret(user.two_factor_secret))
    current_step = int(datetime.now(timezone.utc).timestamp() // totp.interval)
    for step in (current_step - 1, current_step, current_step + 1):
        if step <= (user.two_factor_last_used_step or -1):
            continue
        if totp.verify(code, for_time=step * totp.interval, valid_window=0):
            user.two_factor_last_used_step = step
            return True
    return False


def _consumir_codigo_recuperacao(user: User, code: str) -> bool:
    code_hash = _recovery_code_hash(code)
    for index, stored_hash in enumerate(user.two_factor_recovery_codes):
        if hmac.compare_digest(code_hash, stored_hash):
            user.two_factor_recovery_codes = [
                stored
                for position, stored in enumerate(user.two_factor_recovery_codes)
                if position != index
            ]
            return True
    return False


def _lock_two_factor_user(user: User, db: Session) -> User:
    locked_user = db.scalar(
        select(User).where(User.id == user.id).with_for_update()
    )
    if locked_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida ou expirada.",
        )
    return locked_user


def _validar_codigo_2fa(user: User, code: str) -> bool:
    if len(code) == 6 and code.isdigit():
        return _validar_codigo_totp(user, code)
    return _consumir_codigo_recuperacao(user, code)


def _email_two_factor_configured() -> bool:
    return bool(settings.resend_api_key and settings.resend_from_email)


def _hash_email_code(challenge_token: str, code: str) -> str:
    return hmac.new(
        settings.jwt_secret.encode(),
        f"taskflow-email-2fa:{challenge_token}:{code}".encode(),
        hashlib.sha256,
    ).hexdigest()


def _send_two_factor_email(address: str, code: str) -> None:
    if not _email_two_factor_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="O envio de códigos por email não está configurado.",
        )

    message = {
        "from": settings.resend_from_email,
        "to": [address],
        "subject": "Código de autenticação TaskFlow",
        "text": (
            f"O seu código de autenticação TaskFlow é {code}. "
            "É válido durante 5 minutos e só pode ser utilizado uma vez. "
            "Se não iniciou esta sessão, ignore este email."
        ),
    }
    request = URLRequest(
        "https://api.resend.com/emails",
        data=json.dumps(message).encode(),
        headers={
            "Authorization": f"Bearer {settings.resend_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            if not 200 <= response.status < 300:
                logger.error("Resend rejeitou o envio do código 2FA: HTTP %s", response.status)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Não foi possível enviar o código por email.",
                )
    except HTTPError as error:
        logger.error("Resend rejeitou o envio do código 2FA: HTTP %s", error.code)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Não foi possível enviar o código por email.",
        ) from error
    except (TimeoutError, URLError) as error:
        logger.error("Falha de comunicação com o Resend ao enviar o código 2FA.")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="O serviço de email não está disponível. Tente novamente.",
        ) from error


def _utc_datetime(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def _consumir_desafio_2fa(challenge_token: str, db: Session) -> None:
    challenge_hash = hashlib.sha256(challenge_token.encode()).hexdigest()
    challenge = db.scalar(
        select(TwoFactorLoginChallenge)
        .where(TwoFactorLoginChallenge.challenge_hash == challenge_hash)
        .with_for_update()
    )
    if challenge is None or challenge.consumed_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Desafio de autenticação inválido ou já utilizado.",
        )
    challenge.consumed_at = datetime.now(timezone.utc)


@router.post("/login", response_model=UserPublic | TwoFactorChallenge)
def login(
    request: Request,
    response: Response,
    dados: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> UserPublic | TwoFactorChallenge:
    """Valida a palavra-passe e, se necessário, inicia um desafio 2FA."""
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

    if user.two_factor_enabled:
        challenge_token = criar_token_desafio_2fa(user)
        now = datetime.now(timezone.utc)
        db.execute(
            delete(TwoFactorLoginChallenge).where(
                TwoFactorLoginChallenge.expires_at <= now
            )
        )
        db.add(
            TwoFactorLoginChallenge(
                challenge_hash=hashlib.sha256(
                    challenge_token.encode()
                ).hexdigest(),
                user_id=user.id,
                expires_at=now + timedelta(minutes=5),
            )
        )
        db.commit()
        response.headers["Cache-Control"] = "no-store"
        return TwoFactorChallenge(
            challenge_token=challenge_token,
            methods=[
                "authenticator",
                *(
                    ["email"]
                    if _email_two_factor_configured()
                    else []
                ),
            ],
        )

    _clear_login_failures(db, fingerprints)
    db.commit()
    set_session_cookies(response, user)
    return user


@router.post("/login/2fa", response_model=UserPublic)
def concluir_login_2fa(
    dados: TwoFactorLoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> User:
    """Conclui o login com código TOTP ou código de recuperação de uso único."""
    user = obter_utilizador_desafio_2fa(dados.challenge_token, db)
    remote_host = request.client.host if request and request.client else "unknown"
    fingerprints = _login_fingerprints(user.email, remote_host)
    if _is_login_blocked(db, fingerprints):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas de acesso. Tente novamente em 15 minutos.",
            headers={"Retry-After": str(int(LOGIN_BLOCK_DURATION.total_seconds()))},
        )

    if not _validar_codigo_2fa(user, dados.code):
        _record_login_failure(db, fingerprints)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código de autenticação inválido.",
        )

    _consumir_desafio_2fa(dados.challenge_token, db)
    _clear_login_failures(db, fingerprints)
    db.commit()
    set_session_cookies(response, user)
    return user


@router.post("/login/2fa/email/request")
def pedir_codigo_2fa_email(
    dados: TwoFactorEmailRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Envia um código temporário ao email após validar o desafio de login."""
    user = obter_utilizador_desafio_2fa(dados.challenge_token, db)
    if not _email_two_factor_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="O envio de códigos por email não está configurado.",
        )

    remote_host = request.client.host if request and request.client else "unknown"
    fingerprints = _login_fingerprints(user.email, remote_host)
    if _is_login_blocked(db, fingerprints):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas de acesso. Tente novamente em 15 minutos.",
            headers={"Retry-After": str(int(LOGIN_BLOCK_DURATION.total_seconds()))},
        )

    challenge_hash = hashlib.sha256(dados.challenge_token.encode()).hexdigest()
    now = datetime.now(timezone.utc)
    db.execute(
        delete(EmailLoginCode).where(EmailLoginCode.expires_at <= now)
    )
    most_recent_code = db.scalar(
        select(EmailLoginCode)
        .where(EmailLoginCode.user_id == user.id)
        .order_by(EmailLoginCode.sent_at.desc())
        .limit(1)
        .with_for_update()
    )
    if most_recent_code is not None:
        retry_after = EMAIL_CODE_RESEND_DELAY - (
            now - _utc_datetime(most_recent_code.sent_at)
        )
        if retry_after.total_seconds() > 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Aguarde antes de pedir outro código por email.",
                headers={"Retry-After": str(int(retry_after.total_seconds()) + 1)},
            )

    email_code = db.scalar(
        select(EmailLoginCode)
        .where(EmailLoginCode.challenge_hash == challenge_hash)
        .with_for_update()
    )
    if email_code is not None:
        if email_code.used_at is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este desafio de autenticação já foi utilizado.",
            )

    code = f"{secrets.randbelow(1_000_000):06d}"
    if email_code is None:
        email_code = EmailLoginCode(
            challenge_hash=challenge_hash,
            user_id=user.id,
            code_hash=_hash_email_code(dados.challenge_token, code),
            expires_at=now + EMAIL_CODE_TTL,
            sent_at=now,
            failed_attempts=0,
        )
        db.add(email_code)
    else:
        email_code.code_hash = _hash_email_code(dados.challenge_token, code)
        email_code.expires_at = now + EMAIL_CODE_TTL
        email_code.sent_at = now
        email_code.failed_attempts = 0

    _send_two_factor_email(user.email, code)
    db.commit()
    response.headers["Cache-Control"] = "no-store"
    return {"message": "Código enviado para o email associado à conta."}


@router.post("/login/2fa/email", response_model=UserPublic)
def concluir_login_2fa_email(
    dados: TwoFactorLoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> User:
    """Valida o código de email de uso único e emite a sessão autenticada."""
    user = obter_utilizador_desafio_2fa(dados.challenge_token, db)
    remote_host = request.client.host if request and request.client else "unknown"
    fingerprints = _login_fingerprints(user.email, remote_host)
    if _is_login_blocked(db, fingerprints):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas de acesso. Tente novamente em 15 minutos.",
            headers={"Retry-After": str(int(LOGIN_BLOCK_DURATION.total_seconds()))},
        )

    challenge_hash = hashlib.sha256(dados.challenge_token.encode()).hexdigest()
    email_code = db.scalar(
        select(EmailLoginCode)
        .where(EmailLoginCode.challenge_hash == challenge_hash)
        .with_for_update()
    )
    now = datetime.now(timezone.utc)
    code_is_valid = (
        email_code is not None
        and email_code.user_id == user.id
        and email_code.used_at is None
        and email_code.failed_attempts < MAX_EMAIL_CODE_FAILURES
        and _utc_datetime(email_code.expires_at) > now
        and hmac.compare_digest(
            email_code.code_hash,
            _hash_email_code(dados.challenge_token, dados.code),
        )
    )

    if not code_is_valid:
        if email_code is not None and email_code.used_at is None:
            email_code.failed_attempts += 1
            if email_code.failed_attempts >= MAX_EMAIL_CODE_FAILURES:
                email_code.used_at = now
        _record_login_failure(db, fingerprints)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código de autenticação inválido ou expirado.",
        )

    email_code.used_at = now
    _consumir_desafio_2fa(dados.challenge_token, db)
    _clear_login_failures(db, fingerprints)
    db.commit()
    set_session_cookies(response, user)
    response.headers["Cache-Control"] = "no-store"
    return user


@router.get("/2fa/status")
def estado_2fa(
    user: User = Depends(obter_utilizador_atual),
) -> dict[str, bool]:
    """Devolve apenas se a autenticação de dois fatores está ativada."""
    return {"enabled": user.two_factor_enabled}


@router.post("/2fa/setup")
def iniciar_configuracao_2fa(
    dados: TwoFactorSetupRequest,
    response: Response,
    user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Gera um segredo temporário e um QR code após confirmar a palavra-passe."""
    user = _lock_two_factor_user(user, db)
    if user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A autenticação de dois fatores já está ativada.",
        )
    if not password_hash.verify(dados.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Palavra-passe atual inválida.",
        )

    secret = pyotp.random_base32()
    user.two_factor_secret = _encrypt_two_factor_secret(secret)
    user.two_factor_last_used_step = None
    user.two_factor_recovery_codes = []
    provisioning_uri = pyotp.TOTP(secret).provisioning_uri(
        name=user.email,
        issuer_name="TaskFlow",
    )
    qr = qrcode.QRCode(box_size=5, border=2)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    image = qr.make_image(image_factory=SvgPathImage)
    image_buffer = BytesIO()
    image.save(image_buffer)
    qr_svg = base64.b64encode(image_buffer.getvalue()).decode()
    db.commit()
    response.headers["Cache-Control"] = "no-store"

    return {
        "secret": secret,
        "qr_svg": f"data:image/svg+xml;base64,{qr_svg}",
    }


@router.post("/2fa/enable")
def ativar_2fa(
    dados: TwoFactorCodeRequest,
    response: Response,
    user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
) -> dict[str, list[str]]:
    """Ativa o segundo fator depois de confirmar um primeiro código TOTP."""
    user = _lock_two_factor_user(user, db)
    if user.two_factor_enabled or not user.two_factor_secret:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Inicie uma nova configuração do autenticador.",
        )
    if not _validar_codigo_totp(user, dados.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código inválido. Verifique a app autenticadora e tente novamente.",
        )

    recovery_codes = [
        secrets.token_urlsafe(12)
        for _ in range(RECOVERY_CODE_COUNT)
    ]
    user.two_factor_enabled = True
    user.two_factor_recovery_codes = [
        _recovery_code_hash(code)
        for code in recovery_codes
    ]
    user.session_version += 1
    db.commit()
    set_session_cookies(response, user)
    response.headers["Cache-Control"] = "no-store"
    return {"recovery_codes": recovery_codes}


@router.post("/2fa/disable", status_code=status.HTTP_204_NO_CONTENT)
def desativar_2fa(
    dados: TwoFactorDisableRequest,
    response: Response,
    user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
) -> Response:
    """Desativa o segundo fator após confirmar palavra-passe e código válido."""
    user = _lock_two_factor_user(user, db)
    if not user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A autenticação de dois fatores não está ativada.",
        )
    if not password_hash.verify(dados.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Palavra-passe atual inválida.",
        )
    if not _validar_codigo_2fa(user, dados.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código de autenticação inválido.",
        )

    user.two_factor_enabled = False
    user.two_factor_secret = None
    user.two_factor_last_used_step = None
    user.two_factor_recovery_codes = []
    user.session_version += 1
    db.commit()
    set_session_cookies(response, user)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


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
