from datetime import datetime, timezone
from typing import Generator

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task
from app.models.user import User
from app.schemas.task import (
    TaskCategory,
    TaskCreate,
    TaskPriority,
    TaskResponse,
    TaskStatus,
    TaskUpdate,
)


router = APIRouter(
    prefix="/tasks",
    tags=["Tarefas"],
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# --------------------------------------------------
# VALIDAR PROJETO
# --------------------------------------------------

def obter_projeto(
    db: Session,
    project_id: int,
    permitir_arquivado: bool = False,
) -> Project:

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
    user_id: int,
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
    project_id: int,
    user_id: int,
) -> User:

    utilizador = obter_utilizador_ativo(
        db,
        user_id,
        "O responsável selecionado não existe.",
    )

    membro = db.get(
        ProjectMember,
        (project_id, user_id),
    )

    if membro is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "O responsável selecionado não pertence "
                "a este projeto."
            ),
        )

    return utilizador


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
    db: Session = Depends(get_db),
):

    obter_projeto(
        db,
        dados.project_id,
    )

    obter_utilizador_ativo(
        db,
        dados.created_by,
        "O utilizador que está a criar a tarefa não existe.",
    )

    if dados.assigned_to is not None:
        validar_membro_projeto(
            db,
            dados.project_id,
            dados.assigned_to,
        )

    tarefa = Task(
        **dados.model_dump(),
    )

    if tarefa.status == "completed":
        tarefa.completed_at = datetime.now(timezone.utc)

    try:
        db.add(tarefa)
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
    project_id: int | None = Query(
        default=None,
        gt=0,
    ),
    assigned_to: int | None = Query(
        default=None,
        gt=0,
    ),
    task_status: TaskStatus | None = Query(
        default=None,
        alias="status",
    ),
    priority: TaskPriority | None = None,
    category: TaskCategory | None = None,
    db: Session = Depends(get_db),
):

    consulta = db.query(Task)

    if project_id is not None:
        consulta = consulta.filter(
            Task.project_id == project_id,
        )

    if assigned_to is not None:
        consulta = consulta.filter(
            Task.assigned_to == assigned_to,
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
        .order_by(
            Task.created_at.desc(),
            Task.id.desc(),
        )
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
    task_id: int,
    db: Session = Depends(get_db),
):

    tarefa = db.get(Task, task_id)

    if tarefa is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarefa não encontrada.",
        )

    return tarefa


# --------------------------------------------------
# ATUALIZAR TAREFA
# --------------------------------------------------

@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
)
def atualizar_tarefa(
    task_id: int,
    dados: TaskUpdate,
    db: Session = Depends(get_db),
):

    tarefa = db.get(Task, task_id)

    if tarefa is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarefa não encontrada.",
        )

    obter_projeto(
        db,
        tarefa.project_id,
    )

    alteracoes = dados.model_dump(
        exclude_unset=True,
    )

    if (
        "assigned_to" in alteracoes
        and alteracoes["assigned_to"] is not None
    ):
        validar_membro_projeto(
            db,
            tarefa.project_id,
            alteracoes["assigned_to"],
        )

    estado_anterior = tarefa.status

    for campo, valor in alteracoes.items():
        setattr(
            tarefa,
            campo,
            valor,
        )

    if tarefa.status == "completed":

        if (
            estado_anterior != "completed"
            or tarefa.completed_at is None
        ):
            tarefa.completed_at = datetime.now(timezone.utc)

    else:
        tarefa.completed_at = None

    try:
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


# --------------------------------------------------
# ELIMINAR TAREFA
# --------------------------------------------------

@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def eliminar_tarefa(
    task_id: int,
    db: Session = Depends(get_db),
):

    tarefa = db.get(Task, task_id)

    if tarefa is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarefa não encontrada.",
        )

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

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )