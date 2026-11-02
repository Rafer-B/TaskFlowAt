
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
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import exigir_administrador, get_db, obter_utilizador_atual
from app.models.user import User
from app.schemas.user import UserCreate, UserPublic, UserRoleUpdate


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


@router.post(
    "/",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
)
def registar_utilizador(
    dados: UserCreate,
    _: User = Depends(exigir_administrador),
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
        role=dados.role,
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
def listar_utilizadores(
    _: User = Depends(exigir_administrador),
    db: Session = Depends(get_db),
):
    return db.query(User).order_by(User.id).all()


@router.patch("/{user_id}/role", response_model=UserPublic)
def atualizar_perfil_utilizador(
    user_id: int,
    dados: UserRoleUpdate,
    current_user: User = Depends(exigir_administrador),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilizador não encontrado.",
        )

    if user.id == current_user.id and dados.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não pode remover o seu próprio acesso de administrador.",
        )

    if user.role == "admin" and dados.role != "admin":
        administradores_ativos = (
            db.query(User)
            .filter(
                User.role == "admin",
                User.is_active.is_(True),
            )
            .order_by(User.id)
            .with_for_update()
            .all()
        )
        if len(administradores_ativos) <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A plataforma precisa de manter pelo menos um administrador ativo.",
            )

    user.role = dados.role
    db.commit()
    db.refresh(user)
    return user


@router.post("/{user_id}/avatar", response_model=UserPublic)
async def carregar_fotografia_perfil(
    user_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(obter_utilizador_atual),
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

    if current_user.id != utilizador.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Só pode alterar a sua própria fotografia.",
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
