
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse

router = APIRouter(prefix="/projects", tags=["Projetos"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_projeto(dados: ProjectCreate, db: Session = Depends(get_db)):
    projeto = Project(
        name=dados.name.strip(),
        description=dados.description,
        created_by=dados.created_by,
    )

    try:
        db.add(projeto)
        db.commit()
        db.refresh(projeto)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Não foi possível criar o projeto. Verifica se o utilizador existe.",
        )

    return projeto


@router.get("/", response_model=list[ProjectResponse])
def listar_projetos(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.id.desc()).all()


@router.get("/{project_id}", response_model=ProjectResponse)
def obter_projeto(project_id: int, db: Session = Depends(get_db)):
    projeto = db.get(Project, project_id)

    if projeto is None:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")

    return projeto


@router.patch("/{project_id}", response_model=ProjectResponse)
def atualizar_projeto(
    project_id: int,
    dados: ProjectUpdate,
    db: Session = Depends(get_db),
):
    projeto = db.get(Project, project_id)

    if projeto is None:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")

    alteracoes = dados.model_dump(exclude_unset=True)

    if "name" in alteracoes and alteracoes["name"] is not None:
        alteracoes["name"] = alteracoes["name"].strip()
        if not alteracoes["name"]:
            raise HTTPException(status_code=422, detail="O nome não pode ficar vazio.")

    novo_estado = alteracoes.get("status", projeto.status)

    if novo_estado == "archived":
        projeto.archived_at = projeto.archived_at or datetime.now(timezone.utc)
    elif "status" in alteracoes:
        projeto.archived_at = None

    for campo, valor in alteracoes.items():
        if campo != "status" or valor is not None:
            setattr(projeto, campo, valor)

    try:
        db.commit()
        db.refresh(projeto)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Não foi possível atualizar o projeto.",
        )

    return projeto


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_projeto(project_id: int, db: Session = Depends(get_db)):
    projeto = db.get(Project, project_id)

    if projeto is None:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")

    try:
        db.delete(projeto)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Não é possível eliminar o projeto. Pode ter tarefas associadas.",
        )
