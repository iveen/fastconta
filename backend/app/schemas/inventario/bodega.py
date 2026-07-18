from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BodegaBase(BaseModel):
    codigo: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=100)
    ubicacion: str | None = Field(None, max_length=200)


class BodegaCreate(BodegaBase):
    pass


class BodegaUpdate(BaseModel):
    codigo: str | None = Field(None, max_length=20)
    nombre: str | None = Field(None, max_length=100)
    ubicacion: str | None = Field(None, max_length=200)


class BodegaResponse(BodegaBase):
    public_id: UUID
    empresa_id: UUID
    is_active: bool
    deleted_at: datetime | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)