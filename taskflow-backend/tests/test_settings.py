import pytest

from app.settings import load_settings


def configurar_ambiente_producao(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TASKFLOW_ENV", "production")
    monkeypatch.setenv("DB_HOST", "db.example.com")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "taskflow_production")
    monkeypatch.setenv("DB_USER", "taskflow")
    monkeypatch.setenv("DB_PASSWORD", "production-test-password")
    monkeypatch.setenv(
        "TASKFLOW_JWT_SECRET",
        "production-test-secret-with-at-least-thirty-two-characters",
    )
    monkeypatch.setenv(
        "TASKFLOW_CORS_ORIGINS",
        "https://app.example.com,https://admin.example.com",
    )
    monkeypatch.delenv("TASKFLOW_COOKIE_SECURE", raising=False)
    monkeypatch.setenv("TASKFLOW_COOKIE_SAMESITE", "lax")
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("RESEND_FROM_EMAIL", raising=False)


def test_production_settings_require_long_jwt_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configurar_ambiente_producao(monkeypatch)
    monkeypatch.setenv("TASKFLOW_JWT_SECRET", "too-short")

    with pytest.raises(RuntimeError, match="pelo menos 32 caracteres"):
        load_settings()


def test_production_settings_require_https_cors_origins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configurar_ambiente_producao(monkeypatch)
    monkeypatch.setenv(
        "TASKFLOW_CORS_ORIGINS",
        "https://app.example.com,http://localhost:3000",
    )

    with pytest.raises(RuntimeError, match="devem usar HTTPS"):
        load_settings()


def test_production_settings_enable_secure_cookies_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configurar_ambiente_producao(monkeypatch)

    configured_settings = load_settings()

    assert configured_settings.cookie_secure is True
    assert configured_settings.cookie_samesite == "lax"
    assert configured_settings.cors_origins == (
        "https://app.example.com",
        "https://admin.example.com",
    )


@pytest.mark.parametrize(
    ("api_key", "from_email"),
    [
        ("re_test_api_key", ""),
        ("", "TaskFlow <security@example.com>"),
    ],
)
def test_resend_settings_must_be_configured_together(
    monkeypatch: pytest.MonkeyPatch,
    api_key: str,
    from_email: str,
) -> None:
    monkeypatch.setenv("RESEND_API_KEY", api_key)
    monkeypatch.setenv("RESEND_FROM_EMAIL", from_email)

    with pytest.raises(
        RuntimeError,
        match="RESEND_API_KEY e RESEND_FROM_EMAIL devem ser configurados em conjunto",
    ):
        load_settings()


def test_resend_settings_are_optional_when_both_are_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("RESEND_FROM_EMAIL", raising=False)

    configured_settings = load_settings()

    assert configured_settings.resend_api_key == ""
    assert configured_settings.resend_from_email == ""


def test_resend_settings_accept_complete_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RESEND_API_KEY", " re_test_api_key ")
    monkeypatch.setenv("RESEND_FROM_EMAIL", " TaskFlow <security@example.com> ")

    configured_settings = load_settings()

    assert configured_settings.resend_api_key == "re_test_api_key"
    assert configured_settings.resend_from_email == "TaskFlow <security@example.com>"