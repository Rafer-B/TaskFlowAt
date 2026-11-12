from dataclasses import replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import jwt
import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app import auth


SECRET = "test-secret-with-more-than-thirty-two-characters"


class FakeDatabase:
    def __init__(self, user: SimpleNamespace) -> None:
        self.user = user

    def get(self, model: object, user_id: object) -> SimpleNamespace | None:
        return self.user if user_id == self.user.id else None


def make_request(method: str, cookie: str, csrf_header: str = "") -> Request:
    headers = [(b"cookie", cookie.encode())]
    if csrf_header:
        headers.append((b"x-csrf-token", csrf_header.encode()))
    return Request(
        {
            "type": "http",
            "method": method,
            "path": "/tasks",
            "headers": headers,
            "query_string": b"",
            "server": ("test", 80),
            "client": ("127.0.0.1", 50000),
            "scheme": "http",
        }
    )


def make_token(user_id: object, version: int = 0) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(user_id),
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "ver": version,
        },
        SECRET,
        algorithm="HS256",
    )


@pytest.fixture
def test_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        auth,
        "settings",
        replace(
            auth.settings,
            jwt_secret=SECRET,
            session_cookie_name="taskflow_session",
            csrf_cookie_name="taskflow_csrf",
        ),
    )


@pytest.mark.parametrize(
    ("csrf_cookie", "csrf_header"),
    [("", ""), ("expected", "different"), ("expected", "")],
)
def test_cookie_mutation_requires_matching_csrf(
    test_settings: None,
    csrf_cookie: str,
    csrf_header: str,
) -> None:
    user_id = uuid4()
    cookie = f"taskflow_session={make_token(user_id)}; taskflow_csrf={csrf_cookie}"

    with pytest.raises(HTTPException) as error:
        auth.obter_utilizador_atual(
            make_request("PATCH", cookie, csrf_header),
            bearer_token=None,
            db=FakeDatabase(SimpleNamespace(id=user_id, is_active=True, session_version=0)),
        )

    assert error.value.status_code == 403


def test_valid_cookie_and_csrf_authenticate_user(test_settings: None) -> None:
    user = SimpleNamespace(id=uuid4(), is_active=True, session_version=0)
    csrf = "random-csrf-value"
    cookie = f"taskflow_session={make_token(user.id)}; taskflow_csrf={csrf}"

    result = auth.obter_utilizador_atual(
        make_request("PATCH", cookie, csrf),
        bearer_token=None,
        db=FakeDatabase(user),
    )

    assert result is user


def test_revoked_session_token_is_rejected(test_settings: None) -> None:
    user = SimpleNamespace(id=uuid4(), is_active=True, session_version=1)
    cookie = f"taskflow_session={make_token(user.id, version=0)}"

    with pytest.raises(HTTPException) as error:
        auth.obter_utilizador_atual(
            make_request("GET", cookie),
            bearer_token=None,
            db=FakeDatabase(user),
        )

    assert error.value.status_code == 401
