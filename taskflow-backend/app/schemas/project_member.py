from typing import Literal

from pydantic import BaseModel, Field


ProjectRole = Literal["owner", "member"]


class ProjectMemberCreate(BaseModel):
    user_id: int = Field(gt=0)
    role: ProjectRole = "member"


class ProjectMemberUpdate(BaseModel):
    role: ProjectRole


class ProjectMemberRoleUpdate(BaseModel):
    role: ProjectRole


class ProjectMemberResponse(BaseModel):
    project_id: int
    user_id: int
    name: str
    email: str
    is_active: bool
    role: ProjectRole
    avatar_url: str | None = None