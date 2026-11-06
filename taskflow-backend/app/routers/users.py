
"""Rotas de contas, perfis, palavras-passe e fotografias de utilizador."""

import logging
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
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth import exigir_administrador, get_db, obter_utilizador_atual
from app.models.calendar_event import CalendarEvent
from app.models.project_member import ProjectMember
from app.models.task import Task
from app.models.task_assignee import TaskAssignee
from app.models.task_work_log import TaskWorkLog
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserPasswordUpdate,
    UserPublic,
    UserRoleUpdate,
    UserStatusUpdate,
    UserUpdate,
)


router = APIRouter(prefix="/users", tags=["Utilizadores"])
logger = logging.getLogger(__name__)


def utilizador_tem_dados_associados(db: Session, user_id: int) -> bool:
    """Impede remover a conta enquanto existir histórico ou uma associação."""
    return (
        db.query(Task.id)
        .filter(or_(Task.created_by == user_id, Task.assigned_to == user_id))
        .first()
        is not None
        or db.query(TaskWorkLog.id)
        .filter(TaskWorkLog.author_id == user_id)
        .first()
        is not None
        or db.query(CalendarEvent.id)
        .filter(CalendarEvent.created_by == user_id)
        .first()
        is not None
        or db.query(Team.id)
        .filter(Team.created_by == user_id)
        .first()
        is not None
        or db.query(ProjectMember.user_id)
        .filter(ProjectMember.user_id == user_id)
        .first()
        is not None
        or db.query(TeamMember.user_id)
        .filter(TeamMember.user_id == user_id)
        .first()
        is not None
        or db.query(TaskAssignee.user_id)
        .filter(TaskAssignee.user_id == user_id)
        .first()
        is not None
    )


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


@router.patch("/me/password", response_model=UserPublic)
def atualizar_palavra_passe(
    dados: UserPasswordUpdate,
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    """Confirma a palavra-passe atual e recusa reutilizá-la como nova."""
    if not password_hash.verify(
        dados.current_password,
        current_user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A palavra-passe atual está incorreta.",
        )

    if password_hash.verify(
        dados.new_password,
        current_user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A nova palavra-passe tem de ser diferente da atual.",
        )

    current_user.password_hash = password_hash.hash(dados.new_password)
    current_user.updated_at = func.now()

    try:
        db.commit()
        db.refresh(current_user)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Não foi possível atualizar a palavra-passe do utilizador.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível atualizar a palavra-passe.",
        )

    return current_user


@router.patch("/me/profile", response_model=UserPublic)
def atualizar_o_proprio_perfil(
    dados: UserUpdate,
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    return guardar_atualizacao_perfil(current_user, dados, db)


@router.patch("/{user_id}", response_model=UserPublic)
def atualizar_utilizador(
    user_id: int,
    dados: UserUpdate,
    _: User = Depends(exigir_administrador),
    db: Session = Depends(get_db),
):
    utilizador = db.get(User, user_id)
    if utilizador is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilizador não encontrado.",
        )

    return guardar_atualizacao_perfil(utilizador, dados, db)


def guardar_atualizacao_perfil(
    utilizador: User,
    dados: UserUpdate,
    db: Session,
) -> User:
    """Valida alterações de nome/email e converte conflitos da base de dados."""
    alteracoes = dados.model_dump(exclude_unset=True)
    if not alteracoes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Indique pelo menos um dado para atualizar.",
        )

    novo_nome = alteracoes.get("name", utilizador.name)
    if "name" in alteracoes:
        if alteracoes["name"] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="O nome não pode ficar vazio.",
            )

    novo_email = utilizador.email
    if "email" in alteracoes:
        if alteracoes["email"] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="O email não pode ficar vazio.",
            )

        email = str(alteracoes["email"]).strip().lower()
        existente = (
            db.query(User)
            .filter(User.email == email, User.id != utilizador.id)
            .first()
        )
        if existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe um utilizador com este email.",
            )
        novo_email = email

    utilizador.name = novo_nome
    utilizador.email = novo_email
    utilizador.updated_at = func.now()
    try:
        db.commit()
        db.refresh(utilizador)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível atualizar: o email pode já existir.",
        )
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Não foi possível atualizar o perfil do utilizador.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível atualizar o perfil do utilizador.",
        )

    return utilizador


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
        # O bloqueio das contas evita remover simultaneamente o último administrador.
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


@router.patch("/{user_id}/status", response_model=UserPublic)
def atualizar_estado_utilizador(
    user_id: int,
    dados: UserStatusUpdate,
    current_user: User = Depends(exigir_administrador),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilizador não encontrado.",
        )

    if user.id == current_user.id and not dados.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não pode desativar a sua própria conta.",
        )

    if user.is_active and not dados.is_active and user.role == "admin":
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

    user.is_active = dados.is_active
    user.updated_at = func.now()
    try:
        db.commit()
        db.refresh(user)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Não foi possível atualizar o estado do utilizador.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível atualizar o estado do utilizador.",
        )

    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def eliminar_utilizador(
    user_id: int,
    current_user: User = Depends(exigir_administrador),
    db: Session = Depends(get_db),
) -> None:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilizador não encontrado.",
        )

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não pode eliminar a sua própria conta.",
        )

    if utilizador_tem_dados_associados(db, user.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Esta conta está associada a dados da plataforma e não pode "
                "ser eliminada. Desative-a para impedir o acesso."
            ),
        )

    if user.is_active and user.role == "admin":
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

    ficheiro_temporario: Path | None = None
    avatar_url = user.avatar_url
    if avatar_url and avatar_url.startswith("/uploads/avatars/"):
        nome_ficheiro = Path(avatar_url).name
        if nome_ficheiro and nome_ficheiro == avatar_url.rsplit("/", 1)[-1]:
            caminho_avatar = (AVATAR_DIR / nome_ficheiro).resolve()
            diretorio_avatars = AVATAR_DIR.resolve()
            if caminho_avatar.parent == diretorio_avatars and caminho_avatar.is_file():
                ficheiro_temporario = caminho_avatar.with_name(
                    f".{caminho_avatar.name}.{uuid4().hex}.deleting",
                )
                try:
                    caminho_avatar.replace(ficheiro_temporario)
                except OSError:
                    logger.exception(
                        "Não foi possível preparar a remoção da fotografia do utilizador.",
                    )
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Não foi possível preparar a eliminação da conta.",
                    )

    try:
        db.delete(user)
        db.commit()
    except IntegrityError:
        db.rollback()
        if ficheiro_temporario is not None and ficheiro_temporario.exists():
            try:
                ficheiro_temporario.replace(AVATAR_DIR / Path(avatar_url or "").name)
            except OSError:
                logger.exception(
                    "Não foi possível restaurar a fotografia após a eliminação recusada.",
                )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Esta conta está associada a dados da plataforma e não pode "
                "ser eliminada. Desative-a para impedir o acesso."
            ),
        )
    except SQLAlchemyError:
        db.rollback()
        if ficheiro_temporario is not None and ficheiro_temporario.exists():
            try:
                ficheiro_temporario.replace(AVATAR_DIR / Path(avatar_url or "").name)
            except OSError:
                logger.exception(
                    "Não foi possível restaurar a fotografia após falha na eliminação.",
                )
        logger.exception("Não foi possível eliminar o utilizador.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível eliminar o utilizador.",
        )

    if ficheiro_temporario is not None:
        try:
            ficheiro_temporario.unlink(missing_ok=True)
        except OSError:
            logger.exception(
                "A conta foi eliminada, mas a fotografia não pôde ser apagada.",
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "A conta foi eliminada, mas não foi possível apagar a "
                    "fotografia armazenada."
                ),
            )


@router.delete("/me/avatar", response_model=UserPublic)
def remover_fotografia_perfil(
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    """Atualiza a conta e remove o ficheiro com possibilidade de o restaurar."""
    caminho_temporario: Path | None = None
    avatar_url = current_user.avatar_url

    if avatar_url and avatar_url.startswith("/uploads/avatars/"):
        nome_ficheiro = Path(avatar_url).name
        if nome_ficheiro and nome_ficheiro == avatar_url.rsplit("/", 1)[-1]:
            caminho = (AVATAR_DIR / nome_ficheiro).resolve()
            diretorio_avatars = AVATAR_DIR.resolve()
            if caminho.parent == diretorio_avatars and caminho.is_file():
                caminho_temporario = caminho.with_name(
                    f".{caminho.name}.{uuid4().hex}.deleting",
                )
                try:
                    # Renomeia antes do commit para que o ficheiro antigo deixe de ser servido.
                    caminho.replace(caminho_temporario)
                except OSError:
                    logger.exception(
                        "Não foi possível preparar a remoção da fotografia de perfil.",
                    )
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Não foi possível remover a fotografia de perfil.",
                    )

    current_user.avatar_url = None
    current_user.updated_at = func.now()
    try:
        # Se a gravação falhar, o bloco de exceção restaura o ficheiro renomeado.
        db.commit()
        db.refresh(current_user)
    except SQLAlchemyError:
        db.rollback()
        if caminho_temporario is not None and caminho_temporario.exists():
            try:
                caminho_temporario.replace(AVATAR_DIR / Path(avatar_url or "").name)
            except OSError:
                logger.exception(
                    "Não foi possível restaurar a fotografia após falha na base de dados.",
                )
        logger.exception("Não foi possível remover a fotografia de perfil da conta.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível remover a fotografia de perfil.",
        )

    if caminho_temporario is not None:
        try:
            caminho_temporario.unlink(missing_ok=True)
        except OSError:
            logger.exception(
                "A fotografia foi removida da conta, mas o ficheiro não pôde ser apagado.",
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "A fotografia foi removida da conta, mas não foi possível "
                    "apagar o ficheiro armazenado."
                ),
            )

    return current_user


@router.post("/{user_id}/avatar", response_model=UserPublic)
async def carregar_fotografia_perfil(
    user_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    """Valida a imagem, grava-a e só então associa o URL público à conta."""
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
