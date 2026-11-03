"""Operações de projetos e gestão dos seus membros e respetivos papéis."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import (
    exigir_administrador,
    exigir_papel_projeto,
    get_db,
    obter_utilizador_atual,
)
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
)
from app.schemas.project_member import (
    ProjectMemberCandidate,
    ProjectMemberCreate,
    ProjectMemberUpdate,
    ProjectMemberResponse,
)

router = APIRouter(prefix="/projects", tags=["Projetos"])


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
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    """Cria o projeto e associa o criador como responsável na mesma transação."""
    utilizador = db.get(User, current_user.id)

    if utilizador is None or not utilizador.is_active:
        raise HTTPException(
            status_code=400,
            detail="O utilizador responsável não existe ou está inativo.",
        )

    projeto = Project(
        name=dados.name.strip(),
        description=dados.description,
        created_by=current_user.id,
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

    return {
        "id": projeto.id,
        "name": projeto.name,
        "description": projeto.description,
        "status": projeto.status,
        "created_by": projeto.created_by,
        "created_at": projeto.created_at,
        "updated_at": projeto.updated_at,
        "archived_at": projeto.archived_at,
        "team_id": projeto.team_id,
        "current_user_role": "owner",
    }


@router.get("/", response_model=list[ProjectResponse])
def listar_projetos(
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    consulta = db.query(Project)
    memberships: dict[int, str] = {}
    if current_user.role != "admin":
        consulta = consulta.join(
            ProjectMember,
            ProjectMember.project_id == Project.id,
        ).filter(ProjectMember.user_id == current_user.id)
    projects = consulta.order_by(Project.id.desc()).all()
    if projects and current_user.role != "admin":
        memberships = {
            membership.project_id: membership.role
            for membership in db.query(ProjectMember)
            .filter(
                ProjectMember.user_id == current_user.id,
                ProjectMember.project_id.in_(
                    [project.id for project in projects],
                ),
            )
            .all()
        }
    return [
        {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "created_by": project.created_by,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "archived_at": project.archived_at,
            "team_id": project.team_id,
            "current_user_role": (
                "admin"
                if current_user.role == "admin"
                else memberships.get(project.id)
            ),
        }
        for project in projects
    ]


@router.get("/{project_id}", response_model=ProjectResponse)
def obter_projeto(
    project_id: int,
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    projeto = db.get(Project, project_id)

    if projeto is None:
        raise HTTPException(
            status_code=404,
            detail="Projeto não encontrado.",
        )

    papel = exigir_papel_projeto(db, project_id, current_user)
    return {
        "id": projeto.id,
        "name": projeto.name,
        "description": projeto.description,
        "status": projeto.status,
        "created_by": projeto.created_by,
        "created_at": projeto.created_at,
        "updated_at": projeto.updated_at,
        "archived_at": projeto.archived_at,
        "team_id": projeto.team_id,
        "current_user_role": papel,
    }


@router.patch("/{project_id}", response_model=ProjectResponse)
def atualizar_projeto(
    project_id: int,
    dados: ProjectUpdate,
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    projeto = db.get(Project, project_id)

    if projeto is None:
        raise HTTPException(
            status_code=404,
            detail="Projeto não encontrado.",
        )

    exigir_papel_projeto(
        db,
        project_id,
        current_user,
        {"admin", "owner"},
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
        # Conserva a primeira data de arquivo; reativar limpa essa data.
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

    papel = exigir_papel_projeto(db, project_id, current_user)
    return {
        "id": projeto.id,
        "name": projeto.name,
        "description": projeto.description,
        "status": projeto.status,
        "created_by": projeto.created_by,
        "created_at": projeto.created_at,
        "updated_at": projeto.updated_at,
        "archived_at": projeto.archived_at,
        "team_id": projeto.team_id,
        "current_user_role": papel,
    }


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def eliminar_projeto(
    project_id: int,
    _: User = Depends(exigir_administrador),
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
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    projeto = db.get(Project, project_id)

    if projeto is None:
        raise HTTPException(
            status_code=404,
            detail="Projeto não encontrado.",
        )
    exigir_papel_projeto(db, project_id, current_user)

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


@router.get(
    "/{project_id}/available-members",
    response_model=list[ProjectMemberCandidate],
)
def listar_utilizadores_disponiveis(
    project_id: int,
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    exigir_papel_projeto(
        db,
        project_id,
        current_user,
        {"admin", "owner"},
    )
    membros_atuais = select(ProjectMember.user_id).where(
        ProjectMember.project_id == project_id,
    )
    utilizadores = (
        db.query(User)
        .filter(
            User.is_active.is_(True),
            ~User.id.in_(membros_atuais),
        )
        .order_by(User.name, User.id)
        .all()
    )
    return [
        {
            "id": utilizador.id,
            "name": utilizador.name,
            "email": utilizador.email,
            "avatar_url": utilizador.avatar_url,
        }
        for utilizador in utilizadores
    ]


@router.post(
    "/{project_id}/members",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def adicionar_membro(
    project_id: int,
    dados: ProjectMemberCreate,
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    projeto = db.get(Project, project_id)

    if projeto is None:
        raise HTTPException(
            status_code=404,
            detail="Projeto não encontrado.",
        )

    exigir_papel_projeto(
        db,
        project_id,
        current_user,
        {"admin", "owner"},
    )

    utilizador = (
        db.get(User, dados.user_id)
        if dados.user_id is not None
        else db.query(User)
        .filter(func.lower(User.email) == str(dados.email).lower())
        .first()
    )

    if utilizador is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Esta conta não existe no TaskFlow. "
                "Peça a um administrador para criar a conta antes de a adicionar."
            ),
        )

    if not utilizador.is_active:
        raise HTTPException(
            status_code=400,
            detail="Não é possível adicionar um utilizador inativo.",
        )

    membro_existente = db.get(
        ProjectMember,
        (project_id, utilizador.id),
    )

    if membro_existente is not None:
        raise HTTPException(
            status_code=409,
            detail="Este utilizador já pertence ao projeto.",
        )

    membro = ProjectMember(
        project_id=project_id,
        user_id=utilizador.id,
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
    current_user: User = Depends(obter_utilizador_atual),
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
    exigir_papel_projeto(
        db,
        project_id,
        current_user,
        {"admin", "owner"},
    )

    if membro.role == "owner" and dados.role != "owner":
        # Impede que uma alteração deixe o projeto sem qualquer responsável.
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
    current_user: User = Depends(obter_utilizador_atual),
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
    exigir_papel_projeto(
        db,
        project_id,
        current_user,
        {"admin", "owner"},
    )

    if membro.role == "owner":
        # A mesma regra aplica-se à remoção do último responsável.
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