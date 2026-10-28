
from fastapi import APIRouter, Depends, HTTPException, status
from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate, UserPublic

router = APIRouter(prefix="/users", tags=["Utilizadores"])
password_hash = PasswordHash.recommended()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
)
def registar_utilizador(
    dados: UserCreate,
    db: Session = Depends(get_db),
):
    email = str(dados.email).lower()

    existente = db.query(User).filter(
        User.email == email
    ).first()

    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um utilizador com este email.",
        )

    utilizador = User(
        name=dados.name.strip(),
        email=email,
        password_hash=password_hash.hash(dados.password),
    )

    try:
        db.add(utilizador)
        db.commit()
        db.refresh(utilizador)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível registar: o email pode já existir.",
        )

    return utilizador


@router.get("/", response_model=list[UserPublic])
def listar_utilizadores(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id).all()
