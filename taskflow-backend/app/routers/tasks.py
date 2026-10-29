
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.project import Project
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse

router = APIRouter(prefix="/tasks", tags=["Tarefas"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_tarefa(dados: TaskCreate, db: Session = Depends(get_db)):
    projeto = db.get(Project, dados.project_id)

    if projeto is None:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")

    tarefa = Task(**dados.model_dump())

    if tarefa.status == "completed":
        tarefa.completed_at = datetime.now(timezone.utc)

    try:
        db.add(tarefa)
        db.commit()
        db.refresh(tarefa)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Não foi possível criar a tarefa. Verifica os IDs dos utilizadores e do projeto.",
        )

    return tarefa


@router.get("/", response_model=list[TaskResponse])
def listar_tarefas(
    project_id: int | None = None,
    db: Session = Depends(get_db),
):
    consulta = db.query(Task)

    if project_id is not None:
        consulta = consulta.filter(Task.project_id == project_id)

    return consulta.order_by(Task.id.desc()).all()


@router.get("/{task_id}", response_model=TaskResponse)
def obter_tarefa(task_id: int, db: Session = Depends(get_db)):
    tarefa = db.get(Task, task_id)

    if tarefa is None:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")

    return tarefa


@router.patch("/{task_id}", response_model=TaskResponse)
def atualizar_tarefa(
    task_id: int,
    dados: TaskUpdate,
    db: Session = Depends(get_db),
):
    tarefa = db.get(Task, task_id)

    if tarefa is None:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")

    alteracoes = dados.model_dump(exclude_unset=True)

    if "title" in alteracoes and alteracoes["title"] is not None:
        alteracoes["title"] = alteracoes["title"].strip()
        if not alteracoes["title"]:
            raise HTTPException(status_code=422, detail="O título não pode ficar vazio.")

    for campo, valor in alteracoes.items():
        setattr(tarefa, campo, valor)

    if "status" in alteracoes:
        if tarefa.status == "completed":
            tarefa.completed_at = tarefa.completed_at or datetime.now(timezone.utc)
        else:
            tarefa.completed_at = None

    try:
        db.commit()
        db.refresh(tarefa)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Não foi possível atualizar a tarefa. Verifica os dados fornecidos.",
        )

    return tarefa


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_tarefa(task_id: int, db: Session = Depends(get_db)):
    tarefa = db.get(Task, task_id)

    if tarefa is None:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")

    db.delete(tarefa)
    db.commit()
