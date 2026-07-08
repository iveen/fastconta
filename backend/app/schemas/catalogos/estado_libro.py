"""Schemas para Estados de Libro SAT"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EstadoLibroBase(BaseModel):
    nombre: str = Field(..., max_length=50)


class EstadoLibroCreate(EstadoLibroBase):
    pass


class EstadoLibroUpdate(BaseModel):
    nombre: str | None = Field(None, max_length=50)


class EstadoLibroResponse(EstadoLibroBase):
    id: int  # ✅ BIGINT
    public_id: UUID  # ✅ UUID público
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None
    created_by: int | None = None  # ✅ BIGINT
    updated_by: int | None = None  # ✅ BIGINT

    model_config = {"from_attributes": True}


class EstadoLibroListResponse(BaseModel):
    id: int  # ✅ BIGINT
    public_id: UUID  # ✅ UUID público
    nombre: str
    is_active: bool

    model_config = {"from_attributes": True}