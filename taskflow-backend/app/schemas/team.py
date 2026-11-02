from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def validar_nome(self):
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("O nome da equipa é obrigatório.")
        if self.description is not None:
            self.description = self.description.strip() or None
        return self


class TeamUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def validar_campos(self):
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("O nome da equipa é obrigatório.")
        if self.name is not None:
            self.name = self.name.strip()
            if not self.name:
                raise ValueError("O nome da equipa é obrigatório.")
        if self.description is not None:
            self.description = self.description.strip() or None
        return self


class TeamProjectResponse(BaseModel):
    id: int
    name: str
    status: str


class TeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    created_by: int
    created_at: datetime
    updated_at: datetime
    member_count: int
    projects: list[TeamProjectResponse]
    can_manage: bool
    can_associate_projects: bool


class TeamMemberCreate(BaseModel):
    user_id: int = Field(gt=0)


class TeamMembersCreate(BaseModel):
    user_ids: list[int] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validar_ids_unicos(self):
        if any(user_id <= 0 for user_id in self.user_ids):
            raise ValueError("Os IDs dos utilizadores devem ser positivos.")
        if len(set(self.user_ids)) != len(self.user_ids):
            raise ValueError("A lista contém utilizadores repetidos.")
        return self


class TeamMemberResponse(BaseModel):
    user_id: int
    name: str
    email: str
    avatar_url: str | None = None


class TeamMemberCandidate(TeamMemberResponse):
    pass
