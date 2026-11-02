from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth import (
    exigir_papel_projeto,
    get_db,
    obter_utilizador_atual,
)
from app.models.calendar_event import CalendarEvent
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.calendar_event import (
    CalendarEventCreate,
    CalendarEventResponse,
    CalendarEventUpdate,
)


router = APIRouter(prefix="/calendar/events", tags=["Calendário"])
EDITABLE_PROJECT_ROLES = {"admin", "owner", "contributor"}


def listar_eventos_visiveis(db: Session, user: User) -> list[CalendarEvent]:
    consulta = db.query(CalendarEvent)

    if user.role != "admin":
        projetos_do_utilizador = (
            db.query(ProjectMember.project_id)
            .filter(ProjectMember.user_id == user.id)
            .subquery()
        )
        consulta = consulta.filter(
            or_(
                CalendarEvent.created_by == user.id,
                CalendarEvent.project_id.in_(projetos_do_utilizador),
            )
        )

    return consulta.order_by(CalendarEvent.start_at, CalendarEvent.id).all()


def validar_acesso_edicao(
    db: Session,
    evento: CalendarEvent,
    user: User,
) -> None:
    if user.role == "admin" or evento.created_by == user.id:
        return

    if evento.project_id is not None:
        exigir_papel_projeto(
            db,
            evento.project_id,
            user,
            {"admin", "owner"},
        )
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Só o criador pode alterar ou eliminar este evento.",
    )


def validar_projeto_evento(
    db: Session,
    project_id: int | None,
    user: User,
) -> None:
    if project_id is None:
        return

    exigir_papel_projeto(db, project_id, user, EDITABLE_PROJECT_ROLES)
    projeto = db.get(Project, project_id)
    if projeto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projeto não encontrado.",
        )
    if projeto.status == "archived":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível adicionar eventos a projetos arquivados.",
        )


@router.get("/", response_model=list[CalendarEventResponse])
def obter_eventos(
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    return listar_eventos_visiveis(db, current_user)


@router.post(
    "/",
    response_model=CalendarEventResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_evento(
    dados: CalendarEventCreate,
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    validar_projeto_evento(db, dados.project_id, current_user)
    evento = CalendarEvent(
        **dados.model_dump(),
        created_by=current_user.id,
    )
    db.add(evento)
    db.commit()
    db.refresh(evento)
    return evento


@router.patch("/{event_id}", response_model=CalendarEventResponse)
def atualizar_evento(
    event_id: int,
    dados: CalendarEventUpdate,
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    evento = db.get(CalendarEvent, event_id)
    if evento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado.",
        )

    validar_acesso_edicao(db, evento, current_user)
    alteracoes = dados.model_dump(exclude_unset=True)

    project_id = alteracoes.get("project_id", evento.project_id)
    if project_id is not None:
        validar_projeto_evento(db, project_id, current_user)

    novo_inicio = alteracoes.get("start_at", evento.start_at)
    novo_fim = alteracoes.get("end_at", evento.end_at)
    if novo_fim <= novo_inicio:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A data de fim deve ser posterior à data de início.",
        )

    for campo, valor in alteracoes.items():
        setattr(evento, campo, valor)

    db.commit()
    db.refresh(evento)
    return evento


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_evento(
    event_id: int,
    current_user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    evento = db.get(CalendarEvent, event_id)
    if evento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado.",
        )

    validar_acesso_edicao(db, evento, current_user)
    db.delete(evento)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
