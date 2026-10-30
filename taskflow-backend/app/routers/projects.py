from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
)
from app.schemas.project_member import (
    ProjectMemberCreate,
    ProjectMemberUpdate,
    ProjectMemberResponse,
)

router = APIRouter(prefix="/projects", tags=["Projetos"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --------------------------------------------------
# PROJETOS
# --------------------------------------------------

@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_projeto(
    dados: ProjectCreate,
    db: Session = Depends(get_db),
):
    utilizador = db.get(User, dados.created_by)

    if utilizador is None or not utilizador.is_active:
        raise HTTPException(
            status_code=400,
            detail="O utilizador responsável não existe ou está inativo.",
        )

    projeto = Project(
        name=dados.name.strip(),
        description=dados.description,
        created_by=dados.created_by,
    )

    try:
        db.add(projeto)
        db.flush()

        # O criador passa automaticamente a ser o owner.
        membro = ProjectMember(
            project_id=projeto.id,
            user_id=utilizador.id,
            role="owner",
        )

        db.add(membro)
        db.commit()
        db.refresh(projeto)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Não foi possível criar o projeto.",
        )

    return projeto


@router.get("/", response_model=list[ProjectResponse])
def listar_projetos(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.id.desc()).all()


@router.get("/{project_id}", response_model=ProjectResponse)
def obter_projeto(
    project_id: int,
    db: Session = Depends(get_db),
):
    projeto = db.get(Project, project_id)

    if projeto is None:
        raise HTTPException(
            status_code=404,
            detail="Projeto não encontrado.",
        )

    return projeto


@router.patch("/{project_id}", response_model=ProjectResponse)
def atualizar_projeto(
    project_id: int,
    dados: ProjectUpdate,
    db: Session = Depends(get_db),
):
    projeto = db.get(Project, project_id)

    if projeto is None:
        raise HTTPException(
            status_code=404,
            detail="Projeto não encontrado.",
        )

    alteracoes = dados.model_dump(exclude_unset=True)

    if "name" in alteracoes and alteracoes["name"] is not None:
        alteracoes["name"] = alteracoes["name"].strip()

        if not alteracoes["name"]:
            raise HTTPException(
                status_code=422,
                detail="O nome não pode ficar vazio.",
            )

    novo_estado = alteracoes.get("status", projeto.status)

    if novo_estado == "archived":
        projeto.archived_at = (
            projeto.archived_at or datetime.now(timezone.utc)
        )
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


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def eliminar_projeto(
    project_id: int,
    db: Session = Depends(get_db),
):
    projeto = db.get(Project, project_id)

    if projeto is None:
        raise HTTPException(
            status_code=404,
            detail="Projeto não encontrado.",
        )

    try:
        db.delete(projeto)
        db.commit()

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "Não é possível eliminar o projeto. "
                "Pode ter tarefas ou membros associados."
            ),
        )


# --------------------------------------------------
# MEMBROS DOS PROJETOS
# --------------------------------------------------

@router.get(
    "/{project_id}/members",
    response_model=list[ProjectMemberResponse],
)
def listar_membros(
    project_id: int,
    db: Session = Depends(get_db),
):
    projeto = db.get(Project, project_id)

    if projeto is None:
        raise HTTPException(
            status_code=404,
            detail="Projeto não encontrado.",
        )

    resultados = (
        db.query(ProjectMember, User)
        .join(User, User.id == ProjectMember.user_id)
        .filter(ProjectMember.project_id == project_id)
        .order_by(ProjectMember.role, User.name)
        .all()
    )

    return [
        {
            "project_id": membro.project_id,
            "user_id": membro.user_id,
            "name": utilizador.name,
            "email": utilizador.email,
            "is_active": utilizador.is_active,
            "role": membro.role,
            "avatar_url": utilizador.avatar_url,
        }
        for membro, utilizador in resultados
    ]


@router.post(
    "/{project_id}/members",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def adicionar_membro(
    project_id: int,
    dados: ProjectMemberCreate,
    db: Session = Depends(get_db),
):
    projeto = db.get(Project, project_id)

    if projeto is None:
        raise HTTPException(
            status_code=404,
            detail="Projeto não encontrado.",
        )

    utilizador = db.get(User, dados.user_id)

    if utilizador is None:
        raise HTTPException(
            status_code=404,
            detail="Utilizador não encontrado.",
        )

    if not utilizador.is_active:
        raise HTTPException(
            status_code=400,
            detail="Não é possível adicionar um utilizador inativo.",
        )

    membro_existente = db.get(
        ProjectMember,
        (project_id, dados.user_id),
    )

    if membro_existente is not None:
        raise HTTPException(
            status_code=409,
            detail="Este utilizador já pertence ao projeto.",
        )

    membro = ProjectMember(
        project_id=project_id,
        user_id=dados.user_id,
        role=dados.role,
    )

    try:
        db.add(membro)
        db.commit()
        db.refresh(membro)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Não foi possível adicionar o membro.",
        )

    return {
        "project_id": membro.project_id,
        "user_id": utilizador.id,
        "name": utilizador.name,
        "email": utilizador.email,
        "is_active": utilizador.is_active,
        "role": membro.role,
        "avatar_url": utilizador.avatar_url,
    }


@router.patch(
    "/{project_id}/members/{user_id}",
    response_model=ProjectMemberResponse,
)
def atualizar_responsabilidade(
    project_id: int,
    user_id: int,
    dados: ProjectMemberUpdate,
    db: Session = Depends(get_db),
):
    membro = db.get(
        ProjectMember,
        (project_id, user_id),
    )

    if membro is None:
        raise HTTPException(
            status_code=404,
            detail="Membro não encontrado neste projeto.",
        )

    if membro.role == "owner" and dados.role == "member":
        total_owners = (
            db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id,
                ProjectMember.role == "owner",
            )
            .count()
        )

        if total_owners <= 1:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Não é possível retirar a responsabilidade "
                    "ao último owner do projeto."
                ),
            )

    membro.role = dados.role

    try:
        db.commit()
        db.refresh(membro)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Não foi possível atualizar a responsabilidade.",
        )

    utilizador = db.get(User, user_id)

    if utilizador is None:
        raise HTTPException(
            status_code=404,
            detail="Utilizador não encontrado.",
        )

    return {
        "project_id": membro.project_id,
        "user_id": utilizador.id,
        "name": utilizador.name,
        "email": utilizador.email,
        "is_active": utilizador.is_active,
        "role": membro.role,
        "avatar_url": utilizador.avatar_url,
    }


@router.delete(
    "/{project_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remover_membro(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
):
    membro = db.get(
        ProjectMember,
        (project_id, user_id),
    )

    if membro is None:
        raise HTTPException(
            status_code=404,
            detail="Membro não encontrado neste projeto.",
        )

    if membro.role == "owner":
        total_owners = (
            db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id,
                ProjectMember.role == "owner",
            )
            .count()
        )

        if total_owners <= 1:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Não é possível remover o último owner "
                    "do projeto. Atribui primeiro outro responsável."
                ),
            )

    try:
        db.delete(membro)
        db.commit()

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Não foi possível remover o membro.",
        )