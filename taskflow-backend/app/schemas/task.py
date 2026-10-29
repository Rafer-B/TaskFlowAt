
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


TaskCategory = Literal[
    "planning",
    "research",
    "design",
    "development",
    "validation",
    "documentation",
]

TaskPriority = Literal["low", "medium", "high"]

TaskStatus = Literal["to_do", "in_progress", "completed", "blocked"]


class TaskCreate(BaseModel):
    project_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    category: TaskCategory = "planning"
    priority: TaskPriority = "medium"
    status: TaskStatus = "to_do"
    assigned_to: int | None = Field(default=None, gt=0)
    created_by: int = Field(gt=0)
    due_date: datetime | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    category: TaskCategory | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    assigned_to: int | None = Field(default=None, gt=0)
    due_date: datetime | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    title: str
    description: str | None
    category: str
    priority: str
    status: str
    assigned_to: int | None
    created_by: int
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
