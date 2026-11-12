"""Rotas de tarefas, progresso, registos de trabalho e respetivos anexos."""

from datetime import datetime, timezone
import logging
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.auth import (
    exigir_papel_projeto,
    get_db,
    obter_utilizador_atual,
)
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task
from app.models.task_assignee import TaskAssignee
from app.models.notification import Notification
from app.models.task_history import TaskHistory
from app.models.task_work_log import TaskWorkLog, TaskWorkLogAttachment
from app.models.user import User
from app.schemas.task import (
    TaskCategory,
    TaskCreate,
    TaskPriority,
    TaskResponse,
    TaskStatus,
    TaskUpdate,
    TaskWorkLogResponse,
)
from app.schemas.activity import TaskHistoryResponse
from app.settings import settings


router = APIRouter(
    prefix="/tasks",
    tags=["Tarefas"],
)
logger = logging.getLogger(__name__)


def _json_value(value: object) -> object:
    if isinstance(value, (UUID, datetime)):
        return str(value) if isinstance(value, UUID) else value.isoformat()
    return value


def _changes_for(values: dict[str, object]) -> dict[str, dict[str, object]]:
    return {
        key: {"new": _json_value(value)}
        for key, value in values.items()
    }


TASK_ATTACHMENTS_DIR = settings.task_attachments_dir
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024
MAX_UPDATE_SIZE = 25 * 1024 * 1024
MAX_ATTACHMENTS_PER_UPDATE = 5
ALLOWED_ATTACHMENT_TYPES = {
    ".csv": {"text/csv", "text/plain", "application/vnd.ms-excel"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream",
    },
    ".jpeg": {"image/jpeg"},
    ".jpg": {"image/jpeg"},
    ".md": {"text/markdown", "text/plain"},
    ".pdf": {"application/pdf"},
    ".png": {"image/png"},
    ".txt": {"text/plain"},
    ".webp": {"image/webp"},
    ".xlsx": {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/octet-stream",
    },
}


# --------------------------------------------------
# VALIDAR PROJETO
# --------------------------------------------------

def obter_projeto(
    db: Session,
    project_id: UUID,
    permitir_arquivado: bool = False,
) -> Project:
    """Obtém o projeto e, por omissão, bloqueia alterações após arquivo."""

    projeto = db.get(Project, project_id)

    if projeto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projeto não encontrado.",
        )

    if (
        not permitir_arquivado
        and projeto.status == "archived"
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Não é possível criar ou alterar tarefas "
                "num projeto arquivado."
            ),
        )

    return projeto


# --------------------------------------------------
# VALIDAR UTILIZADOR ATIVO
# --------------------------------------------------

def obter_utilizador_ativo(
    db: Session,
    user_id: UUID,
    mensagem: str = "Utilizador não encontrado.",
) -> User:

    utilizador = db.get(User, user_id)

    if utilizador is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=mensagem,
        )

    if not utilizador.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O utilizador está inativo.",
        )

    return utilizador


# --------------------------------------------------
# VALIDAR MEMBRO DO PROJETO
# --------------------------------------------------

def validar_membro_projeto(
    db: Session,
    project_id: UUID,
    user_id: UUID,
) -> User:
    """Garante que o membro escolhido pertence ao projeto e não é observador."""

    utilizador = obter_utilizador_ativo(
        db,
        user_id,
        "O membro selecionado não existe.",
    )

    membro = db.get(
        ProjectMember,
        (project_id, user_id),
    )

    if membro is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "O membro selecionado não pertence "
                "a este projeto."
            ),
        )
    if membro.role == "viewer":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Um observador não pode ser associado a uma tarefa.",
        )

    return utilizador


def validar_membros_projeto(
    db: Session,
    project_id: UUID,
    user_ids: list[UUID],
) -> None:
    """Garante que todos os membros atribuídos são elegíveis para a tarefa."""
    for user_id in user_ids:
        validar_membro_projeto(db, project_id, user_id)


def obter_tarefa_acessivel(
    db: Session,
    task_id: UUID,
    current_user: User,
    papeis_permitidos: set[str] | None = None,
) -> Task:
    """Carrega a tarefa e aplica ao seu projeto as permissões pedidas."""
    tarefa = db.get(Task, task_id)

    if tarefa is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarefa não encontrada.",
        )
    exigir_papel_projeto(
        db,
        tarefa.project_id,
        current_user,
        papeis_permitidos,
    )

    return tarefa


def limpar_ficheiros(paths: list[Path]) -> None:
    """Remove anexos escritos antes de uma transação falhada, sem mascarar erros."""
    for path in paths:
        try:
            path.unlink(missing_ok=True)
            parent = path.parent
            if parent.exists() and not any(parent.iterdir()):
                parent.rmdir()
        except OSError:
            logger.exception("Não foi possível limpar um anexo temporário.")


# --------------------------------------------------
# CRIAR TAREFA
# --------------------------------------------------

@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_tarefa(
    dados: TaskCreate,
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):

    papel_projeto = exigir_papel_projeto(
        db,
        dados.project_id,
        current_user,
        {"admin", "owner", "contributor"},
    )
    obter_projeto(db, dados.project_id)

    assignee_ids = (
        dados.assignee_ids
        if dados.assignee_ids is not None
        else ([dados.assigned_to] if dados.assigned_to is not None else [])
    )
    if assignee_ids and papel_projeto not in {"admin", "owner"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Só o responsável do projeto pode atribuir tarefas a membros.",
        )
    validar_membros_projeto(db, dados.project_id, assignee_ids)

    tarefa = Task(
        **dados.model_dump(exclude={"assignee_ids", "assigned_to"}),
        assigned_to=assignee_ids[0] if assignee_ids else None,
        created_by=current_user.id,
    )
    tarefa.assignees = [
        TaskAssignee(user_id=user_id)
        for user_id in assignee_ids
    ]

    if tarefa.status == "completed":
        # O estado concluído tem sempre progresso total e uma data de conclusão.
        tarefa.completed_at = datetime.now(timezone.utc)
        tarefa.progress = 100

    try:
        db.add(tarefa)
        db.flush()
        db.add(
            TaskHistory(
                task_id=tarefa.id,
                actor_id=current_user.id,
                action="created",
                changes=_changes_for(
                    {
                        "title": tarefa.title,
                        "status": tarefa.status,
                        "priority": tarefa.priority,
                        "assigned_to": tarefa.assigned_to,
                    }
                ),
            )
        )
        if tarefa.assigned_to is not None and tarefa.assigned_to != current_user.id:
            db.add(
                Notification(
                    recipient_id=tarefa.assigned_to,
                    task_id=tarefa.id,
                    kind="task_assigned",
                    title="Nova tarefa atribuída",
                    message=f"Foste designado para «{tarefa.title}».",
                    target=f"/tasks?taskId={tarefa.id}",
                )
            )
        db.commit()
        db.refresh(tarefa)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Não foi possível criar a tarefa. "
                "Verifica os dados fornecidos."
            ),
        )

    return tarefa


# --------------------------------------------------
# LISTAR TAREFAS
# --------------------------------------------------

@router.get(
    "/",
    response_model=list[TaskResponse],
)
def listar_tarefas(
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    project_id: UUID | None = Query(
        default=None,
    ),
    assigned_to: UUID | None = Query(
        default=None,
    ),
    task_status: TaskStatus | None = Query(
        default=None,
        alias="status",
    ),
    priority: TaskPriority | None = None,
    category: TaskCategory | None = None,
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):

    consulta = db.query(Task)
    if current_user.role != "admin":
        consulta = consulta.join(
            ProjectMember,
            ProjectMember.project_id == Task.project_id,
        ).filter(ProjectMember.user_id == current_user.id)

    if project_id is not None:
        consulta = consulta.filter(
            Task.project_id == project_id,
        )

    if assigned_to is not None:
        consulta = consulta.filter(
            or_(
                Task.assigned_to == assigned_to,
                Task.assignees.any(
                    TaskAssignee.user_id == assigned_to,
                ),
            ),
        )

    if task_status is not None:
        consulta = consulta.filter(
            Task.status == task_status,
        )

    if priority is not None:
        consulta = consulta.filter(
            Task.priority == priority,
        )

    if category is not None:
        consulta = consulta.filter(
            Task.category == category,
        )

    return (
        consulta
        .options(selectinload(Task.assignees))
        .order_by(
            Task.created_at.desc(),
            Task.id.desc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )


# --------------------------------------------------
# CONSULTAR UMA TAREFA
# --------------------------------------------------

@router.get(
    "/{task_id}",
    response_model=TaskResponse,
)
def obter_tarefa(
    task_id: UUID,
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):

    tarefa = db.get(Task, task_id)

    if tarefa is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarefa não encontrada.",
        )

    exigir_papel_projeto(db, tarefa.project_id, current_user)
    return tarefa


# --------------------------------------------------
# ATUALIZAR TAREFA
# --------------------------------------------------

@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
)
def atualizar_tarefa(
    task_id: UUID,
    dados: TaskUpdate,
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):

    tarefa = obter_tarefa_acessivel(
        db,
        task_id,
        current_user,
        {"admin", "owner", "contributor"},
    )

    alteracoes = dados.model_dump(exclude_unset=True)
    alteracoes_hist = {
        campo: {
            "old": _json_value(getattr(tarefa, campo)),
            "new": _json_value(valor),
        }
        for campo, valor in alteracoes.items()
        if getattr(tarefa, campo) != valor
    }
    responsavel_anterior = tarefa.assigned_to

    obter_projeto(
        db,
        tarefa.project_id,
    )

    if "assignee_ids" in alteracoes or "assigned_to" in alteracoes:
        exigir_papel_projeto(
            db,
            tarefa.project_id,
            current_user,
            {"admin", "owner"},
        )
        assignee_ids = (
            alteracoes.pop("assignee_ids")
            if "assignee_ids" in alteracoes
            else (
                [alteracoes["assigned_to"]]
                if alteracoes["assigned_to"] is not None
                else []
            )
        )
        alteracoes.pop("assigned_to", None)
        assignee_ids = assignee_ids or []
        validar_membros_projeto(db, tarefa.project_id, assignee_ids)
        tarefa.assignees = [
            TaskAssignee(user_id=user_id)
            for user_id in assignee_ids
        ]
        tarefa.assigned_to = assignee_ids[0] if assignee_ids else None

    estado_anterior = tarefa.status

    for campo, valor in alteracoes.items():
        setattr(
            tarefa,
            campo,
            valor,
        )

    if tarefa.status == "completed":
        # Mantém o progresso e a data coerentes ao concluir ou reabrir a tarefa.
        tarefa.progress = 100

        if (
            estado_anterior != "completed"
            or tarefa.completed_at is None
        ):
            tarefa.completed_at = datetime.now(timezone.utc)

    else:
        tarefa.completed_at = None

    try:
        if alteracoes_hist:
            db.add(
                TaskHistory(
                    task_id=tarefa.id,
                    actor_id=current_user.id,
                    action="updated",
                    changes=alteracoes_hist,
                )
            )
        novo_responsavel = tarefa.assigned_to
        if (
            novo_responsavel is not None
            and novo_responsavel != responsavel_anterior
            and novo_responsavel != current_user.id
        ):
            db.add(
                Notification(
                    recipient_id=novo_responsavel,
                    task_id=tarefa.id,
                    kind="task_assigned",
                    title="Tarefa atribuída a ti",
                    message=f"Foste designado para «{tarefa.title}».",
                    target=f"/tasks?taskId={tarefa.id}",
                )
            )
        db.commit()
        db.refresh(tarefa)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Não foi possível atualizar a tarefa. "
                "Verifica os dados fornecidos."
            ),
        )

    return tarefa


@router.get(
    "/{task_id}/history",
    response_model=list[TaskHistoryResponse],
)
def listar_historico_tarefa(
    task_id: UUID,
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    tarefa = obter_tarefa_acessivel(db, task_id, current_user)
    rows = db.execute(
        select(TaskHistory, User.name)
        .join(User, User.id == TaskHistory.actor_id)
        .where(TaskHistory.task_id == tarefa.id)
        .order_by(TaskHistory.created_at.desc(), TaskHistory.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return [
        {
            "id": history.id,
            "task_id": history.task_id,
            "actor_id": history.actor_id,
            "actor_name": actor_name,
            "action": history.action,
            "changes": history.changes,
            "created_at": history.created_at,
        }
        for history, actor_name in rows
    ]


# --------------------------------------------------
# REGISTO DE TRABALHO E ANEXOS
# --------------------------------------------------

@router.get(
    "/{task_id}/work-logs",
    response_model=list[TaskWorkLogResponse],
)
def listar_registos_trabalho(
    task_id: UUID,
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    obter_tarefa_acessivel(db, task_id, current_user)

    registos = (
        db.query(TaskWorkLog)
        .options(
            selectinload(TaskWorkLog.author),
            selectinload(TaskWorkLog.attachments),
        )
        .filter(TaskWorkLog.task_id == task_id)
        .order_by(TaskWorkLog.created_at.desc(), TaskWorkLog.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": registo.id,
            "task_id": registo.task_id,
            "author_id": registo.author_id,
            "author_name": registo.author.name,
            "note": registo.note,
            "progress": registo.progress,
            "created_at": registo.created_at,
            "attachments": registo.attachments,
        }
        for registo in registos
    ]


@router.post(
    "/{task_id}/work-logs",
    response_model=TaskWorkLogResponse,
    status_code=status.HTTP_201_CREATED,
)
async def registar_trabalho(
    task_id: UUID,
    note: str = Form(min_length=1, max_length=5000),
    progress: int = Form(ge=0, le=100),
    files: list[UploadFile] | None = File(default=None),
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    tarefa = obter_tarefa_acessivel(
        db,
        task_id,
        current_user,
        {"admin", "owner", "contributor"},
    )
    obter_projeto(db, tarefa.project_id)

    if tarefa.status == "completed" and progress != 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uma tarefa concluída deve manter o progresso a 100%.",
        )

    note = note.strip()
    if not note:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Descreve o trabalho realizado antes de guardar.",
        )

    uploads = [ficheiro for ficheiro in (files or []) if ficheiro.filename]
    if len(uploads) > MAX_ATTACHMENTS_PER_UPDATE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Podes anexar no máximo {MAX_ATTACHMENTS_PER_UPDATE} ficheiros por registo.",
        )

    # Primeiro valida todos os ficheiros em memória; só depois começa a gravá-los.
    preparados: list[tuple[str, str, bytes]] = []
    tamanho_total = 0

    for ficheiro in uploads:
        nome_original = Path(
            (ficheiro.filename or "").replace("\\", "/"),
        ).name
        extensao = Path(nome_original).suffix.lower()
        tipo_conteudo = ficheiro.content_type or ""

        if (
            len(nome_original) > 255
            or extensao not in ALLOWED_ATTACHMENT_TYPES
            or tipo_conteudo not in ALLOWED_ATTACHMENT_TYPES[extensao]
        ):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=(
                    f"O ficheiro “{nome_original}” não é suportado. "
                    "Usa PDF, imagens PNG/JPG/WEBP, TXT, MD, CSV, DOCX ou XLSX."
                ),
            )

        conteudo = await ficheiro.read(MAX_ATTACHMENT_SIZE + 1)
        if len(conteudo) > MAX_ATTACHMENT_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Cada ficheiro pode ter no máximo {MAX_ATTACHMENT_SIZE // (1024 * 1024)} MB.",
            )

        tamanho_total += len(conteudo)
        if tamanho_total > MAX_UPDATE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="O conjunto de anexos não pode ultrapassar 25 MB.",
            )

        preparados.append((nome_original, tipo_conteudo, conteudo))

    caminhos_criados: list[Path] = []
    registo = TaskWorkLog(
        task_id=tarefa.id,
        author_id=current_user.id,
        note=note,
        progress=progress,
    )

    try:
        db.add(registo)
        # O flush obtém o ID do registo antes de criar caminhos de anexos associados.
        db.flush()

        for nome_original, tipo_conteudo, conteudo in preparados:
            extensao = Path(nome_original).suffix.lower()
            nome_guardado = f"{uuid4().hex}{extensao}"
            caminho_relativo = (
                Path(str(tarefa.id))
                / str(registo.id)
                / nome_guardado
            )
            caminho = TASK_ATTACHMENTS_DIR / caminho_relativo
            caminho.parent.mkdir(parents=True, exist_ok=True)
            caminhos_criados.append(caminho)
            caminho.write_bytes(conteudo)

            db.add(
                TaskWorkLogAttachment(
                    work_log_id=registo.id,
                    original_name=nome_original,
                    stored_path=caminho_relativo.as_posix(),
                    content_type=tipo_conteudo,
                    size=len(conteudo),
                ),
            )

        tarefa.progress = progress
        # O registo de trabalho também conta como atividade recente da tarefa.
        tarefa.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(registo)

    except Exception:
        # Base de dados e ficheiros são revertidos em conjunto na medida possível.
        db.rollback()
        limpar_ficheiros(caminhos_criados)
        logger.exception("Não foi possível guardar o registo de trabalho.")
        raise

    return {
        "id": registo.id,
        "task_id": registo.task_id,
        "author_id": registo.author_id,
        "author_name": current_user.name,
        "note": registo.note,
        "progress": registo.progress,
        "created_at": registo.created_at,
        "attachments": registo.attachments,
    }


@router.get(
    "/{task_id}/work-logs/{work_log_id}/attachments/{attachment_id}",
)
def descarregar_anexo_registo(
    task_id: UUID,
    work_log_id: UUID,
    attachment_id: UUID,
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    obter_tarefa_acessivel(db, task_id, current_user)

    anexo = (
        db.query(TaskWorkLogAttachment)
        .join(TaskWorkLog)
        .filter(
            TaskWorkLogAttachment.id == attachment_id,
            TaskWorkLog.id == work_log_id,
            TaskWorkLog.task_id == task_id,
        )
        .first()
    )
    if anexo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anexo não encontrado.",
        )

    raiz_anexos = TASK_ATTACHMENTS_DIR.resolve()
    caminho = (raiz_anexos / anexo.stored_path).resolve()
    if raiz_anexos not in caminho.parents or not caminho.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="O ficheiro anexado já não está disponível.",
        )

    return FileResponse(
        caminho,
        media_type=anexo.content_type,
        filename=anexo.original_name,
        content_disposition_type="attachment",
    )


# --------------------------------------------------
# ELIMINAR TAREFA
# --------------------------------------------------

@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def eliminar_tarefa(
    task_id: UUID,
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):

    tarefa = obter_tarefa_acessivel(
        db,
        task_id,
        current_user,
        {"admin", "owner"},
    )

    anexos = (
        db.query(TaskWorkLogAttachment)
        .join(TaskWorkLog)
        .filter(TaskWorkLog.task_id == task_id)
        .all()
    )
    caminhos_anexos = [
        TASK_ATTACHMENTS_DIR / anexo.stored_path
        for anexo in anexos
    ]

    try:
        db.delete(tarefa)
        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Não foi possível eliminar a tarefa "
                "porque existem registos associados."
            ),
        )

    limpar_ficheiros(caminhos_anexos)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )