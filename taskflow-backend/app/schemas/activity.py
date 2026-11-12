"""Contratos para notificações e histórico de tarefas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    task_id: UUID | None
    kind: str
    title: str
    message: str
    target: str
    created_at: datetime
    read_at: datetime | None


class TaskHistoryResponse(BaseModel):
    id: UUID
    task_id: UUID
    actor_id: UUID
    actor_name: str
    action: str
    changes: dict[str, dict[str, object]]
    created_at: datetime
