"""Configuração validada da aplicação a partir do ambiente."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")


def _boolean(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    if value.lower() not in {"true", "false", "1", "0", "yes", "no"}:
        raise RuntimeError(f"{name} deve ser true ou false.")
    return value.lower() in {"true", "1", "yes"}


@dataclass(frozen=True)
class Settings:
    environment: str
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    jwt_secret: str
    cors_origins: tuple[str, ...]
    cookie_secure: bool
    cookie_samesite: str
    cookie_domain: str | None
    uploads_dir: Path
    task_attachments_dir: Path
    backup_dir: Path
    backup_retention_days: int
    session_cookie_name: str = "taskflow_session"
    csrf_cookie_name: str = "taskflow_csrf"
    session_lifetime_minutes: int = 60
    resend_api_key: str = ""
    resend_from_email: str = ""


def load_settings() -> Settings:
    environment = os.getenv("TASKFLOW_ENV", "development").lower()
    if environment not in {"development", "test", "production"}:
        raise RuntimeError("TASKFLOW_ENV deve ser development, test ou production.")

    secret = os.getenv("TASKFLOW_JWT_SECRET", "")
    if environment == "production" and len(secret) < 32:
        raise RuntimeError(
            "TASKFLOW_JWT_SECRET deve ter pelo menos 32 caracteres em produção."
        )

    raw_origins = os.getenv(
        "TASKFLOW_CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    origins = tuple(origin.strip().rstrip("/") for origin in raw_origins.split(",") if origin.strip())
    if not origins or "*" in origins:
        raise RuntimeError("TASKFLOW_CORS_ORIGINS deve conter origens explícitas.")
    if environment == "production" and any(
        not origin.startswith("https://") for origin in origins
    ):
        raise RuntimeError("As origens CORS de produção devem usar HTTPS.")

    same_site = os.getenv("TASKFLOW_COOKIE_SAMESITE", "lax").lower()
    if same_site not in {"lax", "strict", "none"}:
        raise RuntimeError("TASKFLOW_COOKIE_SAMESITE deve ser lax, strict ou none.")
    cookie_secure = _boolean(
        "TASKFLOW_COOKIE_SECURE",
        environment == "production",
    )
    if same_site == "none" and not cookie_secure:
        raise RuntimeError("Cookies SameSite=None exigem TASKFLOW_COOKIE_SECURE=true.")

    try:
        port = int(os.getenv("DB_PORT", "5432"))
        retention_days = int(os.getenv("TASKFLOW_BACKUP_RETENTION_DAYS", "14"))
    except ValueError as error:
        raise RuntimeError("DB_PORT e TASKFLOW_BACKUP_RETENTION_DAYS devem ser inteiros.") from error
    if not 1 <= port <= 65535 or retention_days < 1:
        raise RuntimeError("Porta PostgreSQL ou retenção de backups inválida.")

    db_user = os.getenv("DB_USER", "")
    db_password = os.getenv("DB_PASSWORD", "")
    if not db_user or not db_password:
        raise RuntimeError("Configura DB_USER e DB_PASSWORD no ficheiro .env")

    return Settings(
        environment=environment,
        db_host=os.getenv("DB_HOST", "localhost"),
        db_port=port,
        db_name=os.getenv("DB_NAME", "taskflowdb_at"),
        db_user=db_user,
        db_password=db_password,
        jwt_secret=secret,
        cors_origins=origins,
        cookie_secure=cookie_secure,
        cookie_samesite=same_site,
        cookie_domain=os.getenv("TASKFLOW_COOKIE_DOMAIN") or None,
        resend_api_key=os.getenv("RESEND_API_KEY", "").strip(),
        resend_from_email=os.getenv("RESEND_FROM_EMAIL", "").strip(),
        uploads_dir=Path(
            os.getenv("TASKFLOW_UPLOADS_DIR", str(BACKEND_DIR / "uploads"))
        ).expanduser().resolve(),
        task_attachments_dir=Path(
            os.getenv(
                "TASKFLOW_TASK_ATTACHMENTS_DIR",
                str(BACKEND_DIR / "task_attachments"),
            )
        ).expanduser().resolve(),
        backup_dir=Path(
            os.getenv("TASKFLOW_BACKUP_DIR", str(BACKEND_DIR / "backups"))
        ).expanduser().resolve(),
        backup_retention_days=retention_days,
    )


settings = load_settings()
