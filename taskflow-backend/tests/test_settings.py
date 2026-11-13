import pytest

from app.settings import load_settings


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