from typing import Literal

from pydantic import BaseModel, EmailStr, Field, model_validator


ProjectRole = Literal["owner", "contributor", "viewer"]


class ProjectMemberCreate(BaseModel):
    user_id: int | None = Field(default=None, gt=0)
    email: EmailStr | None = None
    role: ProjectRole = "contributor"

    @model_validator(mode="after")
    def validar_identificador(self):
        if (self.user_id is None) == (self.email is None):
            raise ValueError("Indica o ID ou o email do utilizador.")
        return self


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


class ProjectMemberCandidate(BaseModel):
    id: int
    name: str
    email: EmailStr
    avatar_url: str | None = None