"""Consulta e atualização das notificações privadas da sessão."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_db, obter_utilizador_atual
from app.models.notification import Notification
from app.models.user import User
from app.schemas.activity import NotificationResponse

router = APIRouter(prefix="/notifications", tags=["Notificações"])


@router.get("/", response_model=list[NotificationResponse])
def listar_notificacoes(
    limit: int = 30,
    offset: int = 0,
    nao_lidas: bool = False,
    user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
) -> list[Notification]:
    if not 1 <= limit <= 100 or offset < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Limite ou deslocamento de notificações inválido.",
        )
    query = select(Notification).where(Notification.recipient_id == user.id)
    if nao_lidas:
        query = query.where(Notification.read_at.is_(None))
    return list(
        db.scalars(
            query.order_by(Notification.created_at.desc(), Notification.id.desc())
            .limit(limit)
            .offset(offset)
        )
    )


@router.get("/unread-count")
def contar_nao_lidas(
    user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    from sqlalchemy import func

    count = db.scalar(
        select(func.count())
        .select_from(Notification)
        .where(
            Notification.recipient_id == user.id,
            Notification.read_at.is_(None),
        )
    )
    return {"count": count or 0}


@router.post("/{notification_id}/read", response_model=NotificationResponse)
def marcar_como_lida(
    notification_id: UUID,
    user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
) -> Notification:
    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.recipient_id == user.id,
        )
    )
    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificação não encontrada.",
        )
    if notification.read_at is None:
        notification.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(notification)
    return notification


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
def marcar_todas_como_lidas(
    user: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
) -> Response:
    db.query(Notification).filter(
        Notification.recipient_id == user.id,
        Notification.read_at.is_(None),
    ).update(
        {Notification.read_at: datetime.now(timezone.utc)},
        synchronize_session=False,
    )
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
