"""Modelos de entrada e saída para eventos e respetiva validação temporal."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


EventColor = Literal["blue", "purple", "green", "red"]


class CalendarEventCreate(BaseModel):
    """Dados de criação; exige datas com fuso e período válido."""

    project_id: UUID | None = None
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    start_at: datetime
    end_at: datetime
    color: EventColor = "purple"

    @model_validator(mode="after")
    def validar_periodo(self):
        """Normaliza texto e rejeita datas sem fuso ou intervalo inválido."""
        if self.start_at.utcoffset() is None or self.end_at.utcoffset() is None:
            raise ValueError("As datas do evento devem incluir o fuso horário.")
        if self.end_at <= self.start_at:
            raise ValueError("A data de fim deve ser posterior à data de início.")
        self.title = self.title.strip()
        if not self.title:
            raise ValueError("O título do evento é obrigatório.")
        if self.description is not None:
            self.description = self.description.strip() or None
        return self


class CalendarEventUpdate(BaseModel):
    """Campos opcionais de edição, distinguindo omissão de valores nulos."""

    project_id: UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    start_at: datetime | None = None
    end_at: datetime | None = None
    color: EventColor | None = None

    @model_validator(mode="after")
    def validar_campos(self):
        """Valida apenas os campos fornecidos e o intervalo quando completo."""
        if "title" in self.model_fields_set and self.title is None:
            raise ValueError("O título do evento é obrigatório.")
        if "start_at" in self.model_fields_set and self.start_at is None:
            raise ValueError("A data de início é obrigatória.")
        if "end_at" in self.model_fields_set and self.end_at is None:
            raise ValueError("A data de fim é obrigatória.")
        if "color" in self.model_fields_set and self.color is None:
            raise ValueError("A cor do evento é obrigatória.")
        if (
            self.start_at is not None
            and self.start_at.utcoffset() is None
        ):
            raise ValueError("A data de início deve incluir o fuso horário.")
        if self.end_at is not None and self.end_at.utcoffset() is None:
            raise ValueError("A data de fim deve incluir o fuso horário.")
        if self.title is not None:
            self.title = self.title.strip()
            if not self.title:
                raise ValueError("O título do evento é obrigatório.")
        if self.description is not None:
            self.description = self.description.strip() or None
        if (
            self.start_at is not None
            and self.end_at is not None
            and self.end_at <= self.start_at
        ):
            raise ValueError("A data de fim deve ser posterior à data de início.")
        return self


class CalendarEventResponse(BaseModel):
    """Representação pública de um evento persistido."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID | None
    title: str
    description: str | None
    start_at: datetime
    end_at: datetime
    color: EventColor
    created_by: UUID
    created_at: datetime
    updated_at: datetime
