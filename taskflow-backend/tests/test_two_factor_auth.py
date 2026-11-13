from dataclasses import replace
import json
from types import SimpleNamespace

import pyotp
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import auth as auth_module
from app import sessions as session_module
from app.auth import get_db
from app.models.email_login_code import EmailLoginCode
from app.models.login_attempt import LoginAttempt
from app.models.two_factor_login_challenge import TwoFactorLoginChallenge
from app.models.user import User
from app.routers import auth as auth_routes
from app.settings import load_settings


SECRET = "test-secret-with-more-than-thirty-two-characters"


def _set_required_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TASKFLOW_ENV", "test")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "taskflow_test")
    monkeypatch.setenv("DB_USER", "taskflow")
    monkeypatch.setenv("DB_PASSWORD", "test-password")
    monkeypatch.setenv("TASKFLOW_JWT_SECRET", SECRET)


@pytest.fixture
def two_factor_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        auth_routes,
        "settings",
        replace(auth_routes.settings, jwt_secret=SECRET),
    )


def test_resend_settings_are_optional_but_must_be_configured_together(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_required_environment(monkeypatch)
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("RESEND_FROM_EMAIL", raising=False)
    assert not load_settings().resend_api_key

    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")
    with pytest.raises(RuntimeError, match="configurados em conjunto"):
        load_settings()

    monkeypatch.setenv("RESEND_FROM_EMAIL", "TaskFlow <security@example.com>")
    config = load_settings()
    assert config.resend_api_key == "re_test_key"
    assert config.resend_from_email == "TaskFlow <security@example.com>"


def test_two_factor_secret_is_encrypted_and_can_be_decrypted(
    two_factor_settings: None,
) -> None:
    secret = pyotp.random_base32()

    encrypted = auth_routes._encrypt_two_factor_secret(secret)

    assert encrypted != secret
    assert auth_routes._decrypt_two_factor_secret(encrypted) == secret


def test_totp_code_can_only_be_used_once(two_factor_settings: None) -> None:
    secret = pyotp.random_base32()
    user = SimpleNamespace(
        two_factor_secret=auth_routes._encrypt_two_factor_secret(secret),
        two_factor_last_used_step=None,
    )
    code = pyotp.TOTP(secret).now()

    assert auth_routes._validar_codigo_totp(user, code)
    assert not auth_routes._validar_codigo_totp(user, code)


def test_recovery_code_is_consumed_on_first_use(two_factor_settings: None) -> None:
    recovery_code = "my-one-time-recovery-code"
    user = SimpleNamespace(
        two_factor_recovery_codes=[
            auth_routes._recovery_code_hash(recovery_code),
        ],
    )

    assert auth_routes._consumir_codigo_recuperacao(user, recovery_code)
    assert not auth_routes._consumir_codigo_recuperacao(user, recovery_code)
    assert user.two_factor_recovery_codes == []


def test_resend_request_sends_email_with_configured_credentials(
    monkeypatch: pytest.MonkeyPatch,
    two_factor_settings: None,
) -> None:
    resend_settings = replace(
        auth_routes.settings,
        resend_api_key="re_test_api_key",
        resend_from_email="TaskFlow <security@example.com>",
    )
    monkeypatch.setattr(auth_routes, "settings", resend_settings)
    captured: dict[str, object] = {}

    class SuccessfulResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["authorization"] = request.get_header("Authorization")
        captured["payload"] = json.loads(request.data)
        captured["timeout"] = timeout
        return SuccessfulResponse()

    monkeypatch.setattr(auth_routes, "urlopen", fake_urlopen)

    auth_routes._send_two_factor_email("person@example.com", "042681")

    assert captured["url"] == "https://api.resend.com/emails"
    assert captured["authorization"] == "Bearer re_test_api_key"
    assert captured["timeout"] == 10
    assert captured["payload"] == {
        "from": "TaskFlow <security@example.com>",
        "to": ["person@example.com"],
        "subject": "Código de autenticação TaskFlow",
        "text": (
            "O seu código de autenticação TaskFlow é 042681. "
            "É válido durante 5 minutos e só pode ser utilizado uma vez. "
            "Se não iniciou esta sessão, ignore este email."
        ),
    }


def test_login_requires_and_accepts_a_second_factor(
    monkeypatch: pytest.MonkeyPatch,
    two_factor_settings: None,
) -> None:
    secure_settings = replace(
        auth_module.settings,
        jwt_secret=SECRET,
        cookie_secure=False,
        resend_api_key="re_test_api_key",
        resend_from_email="TaskFlow <security@example.com>",
    )
    monkeypatch.setattr(auth_module, "settings", secure_settings)
    monkeypatch.setattr(session_module, "settings", secure_settings)
    monkeypatch.setattr(auth_routes, "settings", secure_settings)
    sent_codes: list[tuple[str, str]] = []
    monkeypatch.setattr(
        auth_routes,
        "_send_two_factor_email",
        lambda address, code: sent_codes.append((address, code)),
    )

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    User.__table__.create(engine)
    LoginAttempt.__table__.create(engine)
    EmailLoginCode.__table__.create(engine)
    TwoFactorLoginChallenge.__table__.create(engine)
    test_session = sessionmaker(bind=engine, expire_on_commit=False)
    secret = pyotp.random_base32()
    user = User(
        name="Two Factor User",
        email="two-factor@example.com",
        password_hash=auth_routes.password_hash.hash("a-secure-password"),
        role="member",
        session_version=0,
        two_factor_secret=auth_routes._encrypt_two_factor_secret(secret),
        two_factor_enabled=True,
        two_factor_recovery_codes=[],
        is_active=True,
    )
    with test_session() as db:
        db.add(user)
        db.commit()

    app = FastAPI()
    app.include_router(auth_routes.router)

    def override_get_db():
        with test_session() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            login_response = client.post(
                "/auth/login",
                data={
                    "username": "two-factor@example.com",
                    "password": "a-secure-password",
                },
            )

            assert login_response.status_code == 200
            challenge = login_response.json()
            assert challenge["requires_two_factor"] is True
            assert "taskflow_session" not in login_response.cookies

            verify_response = client.post(
                "/auth/login/2fa",
                json={
                    "challenge_token": challenge["challenge_token"],
                    "code": pyotp.TOTP(secret).now(),
                },
            )

            assert verify_response.status_code == 200
            assert verify_response.json()["email"] == "two-factor@example.com"
            assert "taskflow_session" in verify_response.cookies

            reused_totp_challenge = client.post(
                "/auth/login/2fa",
                json={
                    "challenge_token": challenge["challenge_token"],
                    "code": pyotp.TOTP(secret).now(),
                },
            )
            assert reused_totp_challenge.status_code == 401

            next_login = client.post(
                "/auth/login",
                data={
                    "username": "two-factor@example.com",
                    "password": "a-secure-password",
                },
            )
            next_challenge = next_login.json()
            assert next_login.status_code == 200
            assert next_challenge["methods"] == ["authenticator", "email"]

            email_request = client.post(
                "/auth/login/2fa/email/request",
                json={"challenge_token": next_challenge["challenge_token"]},
            )
            assert email_request.status_code == 200
            assert sent_codes[-1][0] == "two-factor@example.com"

            throttled_request = client.post(
                "/auth/login/2fa/email/request",
                json={"challenge_token": next_challenge["challenge_token"]},
            )
            assert throttled_request.status_code == 429

            email_verify = client.post(
                "/auth/login/2fa/email",
                json={
                    "challenge_token": next_challenge["challenge_token"],
                    "code": sent_codes[-1][1],
                },
            )
            assert email_verify.status_code == 200
            assert email_verify.json()["email"] == "two-factor@example.com"

            reused_email_code = client.post(
                "/auth/login/2fa/email",
                json={
                    "challenge_token": next_challenge["challenge_token"],
                    "code": sent_codes[-1][1],
                },
            )
            assert reused_email_code.status_code == 401
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
