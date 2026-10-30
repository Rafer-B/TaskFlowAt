from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import SessionLocal
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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=list[ProjectMemberResponse])
def list_project_members(
    project_id: int,
    db: Session = Depends(get_db)
):
    project = db.get(Project, project_id)

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Projeto não encontrado."
        )

    statement = (
        select(ProjectMember, User)
        .join(User, User.id == ProjectMember.user_id)
        .where(ProjectMember.project_id == project_id)
        .order_by(User.name)
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
    project_id: int,
    data: ProjectMemberCreate,
    db: Session = Depends(get_db)
):
    project = db.get(Project, project_id)

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Projeto não encontrado."
        )

    user = db.get(User, data.user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Utilizador não encontrado."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=400,
            detail="Não é possível adicionar um utilizador inativo."
        )

    existing_member = db.get(
        ProjectMember,
        (project_id, data.user_id)
    )

    if existing_member:
        raise HTTPException(
            status_code=409,
            detail="Este utilizador já pertence ao projeto."
        )

    member = ProjectMember(
        project_id=project_id,
        user_id=data.user_id,
        role=data.role
    )

    db.add(member)

    try:
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
    project_id: int,
    user_id: int,
    data: ProjectMemberRoleUpdate,
    db: Session = Depends(get_db)
):
    member = db.get(ProjectMember, (project_id, user_id))

    if not member:
        raise HTTPException(
            status_code=404,
            detail="Membro não encontrado neste projeto."
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
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    member = db.get(ProjectMember, (project_id, user_id))

    if not member:
        raise HTTPException(
            status_code=404,
            detail="Membro não encontrado neste projeto."
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