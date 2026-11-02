from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import exigir_papel_projeto, get_db, obter_utilizador_atual
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas.team import (
    TeamCreate,
    TeamMemberCandidate,
    TeamMemberCreate,
    TeamMembersCreate,
    TeamMemberResponse,
    TeamResponse,
    TeamUpdate,
)


router = APIRouter(prefix="/teams", tags=["Equipas"])


def pode_gerir_equipa(db: Session, team: Team, user: User) -> bool:
    if user.role == "admin" or team.created_by == user.id:
        return True

    return (
        db.query(ProjectMember)
        .join(Project, Project.id == ProjectMember.project_id)
        .filter(
            Project.team_id == team.id,
            ProjectMember.user_id == user.id,
            ProjectMember.role == "owner",
        )
        .first()
        is not None
    )


def pode_associar_projetos(db: Session, team: Team, user: User) -> bool:
    if pode_gerir_equipa(db, team, user):
        return True
    return (
        db.query(ProjectMember)
        .filter(
            ProjectMember.user_id == user.id,
            ProjectMember.role == "owner",
        )
        .first()
        is not None
    )


def obter_equipa_visivel(db: Session, team_id: int, user: User) -> Team:
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipa não encontrada.",
        )

    if (
        user.role == "admin"
        or team.created_by == user.id
        or pode_associar_projetos(db, team, user)
    ):
        return team

    is_member = (
        db.query(TeamMember)
        .filter(
            TeamMember.team_id == team.id,
            TeamMember.user_id == user.id,
        )
        .first()
    )
    is_project_member = (
        db.query(ProjectMember)
        .join(Project, Project.id == ProjectMember.project_id)
        .filter(
            Project.team_id == team.id,
            ProjectMember.user_id == user.id,
        )
        .first()
    )
    if is_member is None and is_project_member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipa não encontrada.",
        )
    return team


def exigir_gestao_equipa(db: Session, team: Team, user: User) -> None:
    if not pode_gerir_equipa(db, team, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Só administradores, criadores e responsáveis dos projetos da equipa podem geri-la.",
        )


def resposta_equipa(db: Session, team: Team, user: User) -> dict:
    projetos = (
        db.query(Project)
        .filter(Project.team_id == team.id)
        .order_by(Project.name, Project.id)
        .all()
    )
    member_count = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team.id)
        .count()
    )
    return {
        "id": team.id,
        "name": team.name,
        "description": team.description,
        "created_by": team.created_by,
        "created_at": team.created_at,
        "updated_at": team.updated_at,
        "member_count": member_count,
        "projects": [
            {"id": project.id, "name": project.name, "status": project.status}
            for project in projetos
        ],
        "can_manage": pode_gerir_equipa(db, team, user),
        "can_associate_projects": pode_associar_projetos(db, team, user),
    }


def resposta_membro(utilizador: User) -> dict:
    return {
        "user_id": utilizador.id,
        "name": utilizador.name,
        "email": utilizador.email,
        "avatar_url": utilizador.avatar_url,
    }


@router.get("/", response_model=list[TeamResponse])
def listar_equipas(
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    consulta = db.query(Team)
    if current_user.role != "admin":
        equipa_com_membro = select(TeamMember.team_id).where(
            TeamMember.user_id == current_user.id,
        )
        projetos_do_utilizador = select(ProjectMember.project_id).where(
            ProjectMember.user_id == current_user.id,
        )
        equipa_de_projeto = select(Project.team_id).where(
            Project.id.in_(projetos_do_utilizador),
            Project.team_id.is_not(None),
        )
        consulta = consulta.filter(
            or_(
                Team.created_by == current_user.id,
                Team.id.in_(equipa_com_membro),
                Team.id.in_(equipa_de_projeto),
                select(ProjectMember.project_id)
                .where(
                    ProjectMember.user_id == current_user.id,
                    ProjectMember.role == "owner",
                )
                .exists(),
            )
        )

    return [
        resposta_equipa(db, team, current_user)
        for team in consulta.order_by(Team.name, Team.id).all()
    ]


@router.post(
    "/",
    response_model=TeamResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_equipa(
    dados: TeamCreate,
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin":
        e_responsavel = (
            db.query(ProjectMember)
            .filter(
                ProjectMember.user_id == current_user.id,
                ProjectMember.role == "owner",
            )
            .first()
        )
        if e_responsavel is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Só administradores ou responsáveis de projetos podem criar equipas.",
            )

    team = Team(
        name=dados.name,
        description=dados.description,
        created_by=current_user.id,
    )
    db.add(team)
    try:
        db.flush()
        db.add(TeamMember(team_id=team.id, user_id=current_user.id))
        db.commit()
        db.refresh(team)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível criar a equipa.",
        )
    return resposta_equipa(db, team, current_user)


@router.get("/{team_id}", response_model=TeamResponse)
def obter_equipa(
    team_id: int,
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    team = obter_equipa_visivel(db, team_id, current_user)
    return resposta_equipa(db, team, current_user)


@router.patch("/{team_id}", response_model=TeamResponse)
def atualizar_equipa(
    team_id: int,
    dados: TeamUpdate,
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    team = obter_equipa_visivel(db, team_id, current_user)
    exigir_gestao_equipa(db, team, current_user)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(team, campo, valor)
    try:
        db.commit()
        db.refresh(team)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível atualizar a equipa.",
        )
    return resposta_equipa(db, team, current_user)


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_equipa(
    team_id: int,
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    team = obter_equipa_visivel(db, team_id, current_user)
    exigir_gestao_equipa(db, team, current_user)
    db.delete(team)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{team_id}/members",
    response_model=list[TeamMemberResponse],
)
def listar_membros(
    team_id: int,
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    team = obter_equipa_visivel(db, team_id, current_user)
    members = (
        db.query(User)
        .join(TeamMember, TeamMember.user_id == User.id)
        .filter(TeamMember.team_id == team.id)
        .order_by(User.name, User.id)
        .all()
    )
    return [resposta_membro(user) for user in members]


@router.get(
    "/{team_id}/available-members",
    response_model=list[TeamMemberCandidate],
)
def listar_utilizadores_disponiveis(
    team_id: int,
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    team = obter_equipa_visivel(db, team_id, current_user)
    exigir_gestao_equipa(db, team, current_user)
    ids_membros = select(TeamMember.user_id).where(
        TeamMember.team_id == team.id,
    )
    return [
        resposta_membro(user)
        for user in (
            db.query(User)
            .filter(
                User.is_active.is_(True),
                ~User.id.in_(ids_membros),
            )
            .order_by(User.name, User.id)
            .all()
        )
    ]


@router.post(
    "/{team_id}/members/bulk",
    response_model=list[TeamMemberResponse],
    status_code=status.HTTP_201_CREATED,
)
def adicionar_membros(
    team_id: int,
    dados: TeamMembersCreate,
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    team = obter_equipa_visivel(db, team_id, current_user)
    exigir_gestao_equipa(db, team, current_user)
    utilizadores = (
        db.query(User)
        .filter(User.id.in_(dados.user_ids))
        .order_by(User.name, User.id)
        .all()
    )
    utilizadores_por_id = {user.id: user for user in utilizadores}
    if len(utilizadores_por_id) != len(dados.user_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Um ou mais utilizadores selecionados não foram encontrados.",
        )
    if any(not user.is_active for user in utilizadores):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível adicionar utilizadores inativos.",
        )
    membros_existentes = (
        db.query(TeamMember.user_id)
        .filter(
            TeamMember.team_id == team.id,
            TeamMember.user_id.in_(dados.user_ids),
        )
        .all()
    )
    if membros_existentes:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Um ou mais utilizadores já pertencem à equipa.",
        )

    db.add_all(
        TeamMember(team_id=team.id, user_id=user_id)
        for user_id in dados.user_ids
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível adicionar os membros à equipa.",
        )
    return [
        resposta_membro(utilizadores_por_id[user_id])
        for user_id in dados.user_ids
    ]


@router.post(
    "/{team_id}/members",
    response_model=TeamMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def adicionar_membro(
    team_id: int,
    dados: TeamMemberCreate,
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    team = obter_equipa_visivel(db, team_id, current_user)
    exigir_gestao_equipa(db, team, current_user)
    user = db.get(User, dados.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilizador não encontrado.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível adicionar um utilizador inativo.",
        )
    if db.get(TeamMember, (team.id, user.id)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este utilizador já pertence à equipa.",
        )
    db.add(TeamMember(team_id=team.id, user_id=user.id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível adicionar o membro à equipa.",
        )
    return resposta_membro(user)


@router.delete(
    "/{team_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remover_membro(
    team_id: int,
    user_id: int,
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    team = obter_equipa_visivel(db, team_id, current_user)
    exigir_gestao_equipa(db, team, current_user)
    membership = db.get(TeamMember, (team.id, user_id))
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membro não encontrado nesta equipa.",
        )
    db.delete(membership)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{team_id}/projects/{project_id}",
    response_model=TeamResponse,
)
def associar_projeto(
    team_id: int,
    project_id: int,
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projeto não encontrado.",
        )
    exigir_papel_projeto(db, project.id, current_user, {"admin", "owner"})
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipa não encontrada.",
        )
    if project.team_id is not None and project.team_id != team.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este projeto já está associado a outra equipa.",
        )
    project.team_id = team.id
    db.commit()
    db.refresh(team)
    return resposta_equipa(db, team, current_user)


@router.delete(
    "/{team_id}/projects/{project_id}",
    response_model=TeamResponse,
)
def desassociar_projeto(
    team_id: int,
    project_id: int,
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    team = obter_equipa_visivel(db, team_id, current_user)
    exigir_gestao_equipa(db, team, current_user)
    project = db.get(Project, project_id)
    if project is None or project.team_id != team.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projeto não encontrado nesta equipa.",
        )
    exigir_papel_projeto(db, project.id, current_user, {"admin", "owner"})
    project.team_id = None
    db.commit()
    db.refresh(team)
    return resposta_equipa(db, team, current_user)
