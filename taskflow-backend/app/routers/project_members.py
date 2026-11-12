"""Rotas de consulta e manutenção de membros associados a um projeto."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import exigir_papel_projeto, get_db, obter_utilizador_atual
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.project_member import (
    ProjectMemberCreate,
    ProjectMemberRoleUpdate,
    ProjectMemberResponse,
)


router = APIRouter(
    prefix="/projects/{project_id}/members",
    tags=["Project Members"]
)


@router.get("/", response_model=list[ProjectMemberResponse])
def list_project_members(
    project_id: UUID,
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db)
):
    project = db.get(Project, project_id)

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Projeto não encontrado."
        )
    exigir_papel_projeto(db, project_id, current_user)

    statement = (
        select(ProjectMember, User)
        .join(User, User.id == ProjectMember.user_id)
        .where(ProjectMember.project_id == project_id)
        .order_by(User.name)
        .offset(offset)
        .limit(limit)
    )

    results = db.execute(statement).all()

    return [
        ProjectMemberResponse(
            project_id=member.project_id,
            user_id=user.id,
            name=user.name,
            email=user.email,
            is_active=user.is_active,
            role=member.role
        )
        for member, user in results
    ]


@router.post(
    "/",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED
)
def add_project_member(
    project_id: UUID,
    data: ProjectMemberCreate,
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db)
):
    """Adiciona uma conta ativa se o autor for administrador ou responsável."""
    project = db.get(Project, project_id)

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Projeto não encontrado."
        )
    exigir_papel_projeto(
        db,
        project_id,
        current_user,
        {"admin", "owner"},
    )

    user = (
        db.get(User, data.user_id)
        if data.user_id is not None
        else db.query(User)
        .filter(func.lower(User.email) == str(data.email).lower())
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail=(
                "Esta conta não existe no TaskFlow. "
                "Peça a um administrador para criar a conta antes de a adicionar."
            )
        )

    if not user.is_active:
        raise HTTPException(
            status_code=400,
            detail="Não é possível adicionar um utilizador inativo."
        )

    existing_member = db.get(
        ProjectMember,
        (project_id, user.id)
    )

    if existing_member:
        raise HTTPException(
            status_code=409,
            detail="Este utilizador já pertence ao projeto."
        )

    member = ProjectMember(
        project_id=project_id,
        user_id=user.id,
        role=data.role
    )

    db.add(member)

    try:
        # A transação trata também corridas que tentem inserir a mesma associação.
        db.commit()
        db.refresh(member)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Não foi possível adicionar o membro."
        )

    return ProjectMemberResponse(
        project_id=member.project_id,
        user_id=user.id,
        name=user.name,
        email=user.email,
        is_active=user.is_active,
        role=member.role
    )


@router.patch("/{user_id}", response_model=ProjectMemberResponse)
def update_project_member_role(
    project_id: UUID,
    user_id: UUID,
    data: ProjectMemberRoleUpdate,
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db)
):
    """Atualiza o papel, preservando sempre pelo menos um responsável."""
    member = db.get(ProjectMember, (project_id, user_id))

    if not member:
        raise HTTPException(
            status_code=404,
            detail="Membro não encontrado neste projeto."
        )
    exigir_papel_projeto(
        db,
        project_id,
        current_user,
        {"admin", "owner"},
    )

    if member.role == "owner" and data.role != "owner":
        owners_count = db.scalar(
            select(func.count())
            .select_from(ProjectMember)
            .where(
                ProjectMember.project_id == project_id,
                ProjectMember.role == "owner"
            )
        )

        if owners_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="O projeto precisa de ter pelo menos um responsável."
            )

    member.role = data.role

    db.commit()
    db.refresh(member)

    user = db.get(User, user_id)

    return ProjectMemberResponse(
        project_id=project_id,
        user_id=user.id,
        name=user.name,
        email=user.email,
        is_active=user.is_active,
        role=member.role
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_project_member(
    project_id: UUID,
    user_id: UUID,
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db)
):
    member = db.get(ProjectMember, (project_id, user_id))

    if not member:
        raise HTTPException(
            status_code=404,
            detail="Membro não encontrado neste projeto."
        )
    exigir_papel_projeto(
        db,
        project_id,
        current_user,
        {"admin", "owner"},
    )

    if member.role == "owner":
        owners_count = db.scalar(
            select(func.count())
            .select_from(ProjectMember)
            .where(
                ProjectMember.project_id == project_id,
                ProjectMember.role == "owner"
            )
        )

        if owners_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Não é possível remover o último responsável do projeto."
            )

    db.delete(member)
    db.commit()

    return None