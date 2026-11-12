"""Cookie de sessão e token CSRF necessários ao fluxo autenticado."""

import secrets

from fastapi import Response

from app.auth import criar_token_acesso
from app.models.user import User
from app.settings import settings


def set_session_cookies(response: Response, user: User) -> None:
    common = {
        "secure": settings.cookie_secure,
        "samesite": settings.cookie_samesite,
        "path": "/",
        "domain": settings.cookie_domain,
        "max_age": settings.session_lifetime_minutes * 60,
    }
    response.set_cookie(
        settings.session_cookie_name,
        criar_token_acesso(user),
        httponly=True,
        **common,
    )
    response.set_cookie(
        settings.csrf_cookie_name,
        secrets.token_urlsafe(32),
        httponly=False,
        **common,
    )


def clear_session_cookies(response: Response) -> None:
    for name in (settings.session_cookie_name, settings.csrf_cookie_name):
        response.delete_cookie(
            name,
            path="/",
            domain=settings.cookie_domain,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
        )
