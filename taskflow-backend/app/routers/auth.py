from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.auth import criar_token_acesso, get_db, obter_utilizador_atual
from app.models.user import User
from app.schemas.auth import AccessToken
from app.schemas.user import UserPublic

router = APIRouter(prefix="/auth", tags=["Autenticação"])
password_hash = PasswordHash.recommended()
DUMMY_PASSWORD_HASH = password_hash.hash("not-a-real-user-password")


@router.post("/login", response_model=AccessToken)
def login(
    dados: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> AccessToken:
    user = db.query(User).filter(
        User.email == dados.username.strip().lower(),
    ).first()

    hash_para_verificar = (
        user.password_hash if user is not None else DUMMY_PASSWORD_HASH
    )
    palavra_passe_valida = password_hash.verify(
        dados.password,
        hash_para_verificar,
    )

    if user is None or not user.is_active or not palavra_passe_valida:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou palavra-passe inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AccessToken(access_token=criar_token_acesso(user))


@router.get("/me", response_model=UserPublic)
def utilizador_atual(
    user: User = Depends(obter_utilizador_atual),
) -> User:
    return user
