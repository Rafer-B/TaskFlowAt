
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate, UserPublic


router = APIRouter(prefix="/users", tags=["Utilizadores"])

password_hash = PasswordHash.recommended()

# Pasta onde serão guardadas as fotografias.
AVATAR_DIR = Path("uploads/avatars")
AVATAR_DIR.mkdir(parents=True, exist_ok=True)

MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5 MB

ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


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


@router.post("/{user_id}/avatar", response_model=UserPublic)
async def carregar_fotografia_perfil(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    utilizador = db.query(User).filter(
        User.id == user_id
    ).first()

    if not utilizador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilizador não encontrado.",
        )

    extensao = ALLOWED_TYPES.get(file.content_type or "")

    if not extensao:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato inválido. Utilize JPG, PNG ou WEBP.",
        )

    conteudo = await file.read(MAX_AVATAR_SIZE + 1)

    if not conteudo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O ficheiro enviado está vazio.",
        )

    if len(conteudo) > MAX_AVATAR_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="A fotografia não pode ultrapassar 5 MB.",
        )

    # Verificação básica da assinatura real do ficheiro.
    assinaturas_validas = {
        "image/jpeg": conteudo.startswith(b"\xff\xd8\xff"),
        "image/png": conteudo.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/webp": (
            len(conteudo) >= 12
            and conteudo.startswith(b"RIFF")
            and conteudo[8:12] == b"WEBP"
        ),
    }

    if not assinaturas_validas.get(file.content_type, False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O conteúdo do ficheiro não corresponde a uma imagem válida.",
        )

    nome_ficheiro = f"{uuid4().hex}{extensao}"
    caminho = AVATAR_DIR / nome_ficheiro

    try:
        caminho.write_bytes(conteudo)

        # Guarda apenas o endereço público, não o caminho físico.
        utilizador.avatar_url = f"/uploads/avatars/{nome_ficheiro}"
        utilizador.updated_at = func.now()

        db.commit()
        db.refresh(utilizador)

    except Exception:
        db.rollback()

        if caminho.exists():
            caminho.unlink()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível guardar a fotografia.",
        )

    return utilizador
