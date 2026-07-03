"""Schemas para Tipos de Persona"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# BASE
# ============================================================
class TipoPersonaBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=50, examples=["NATURAL"])
    descripcion: str | None = Field(None, max_length=200)


class TipoPersonaCreate(TipoPersonaBase):
    pass


class TipoPersonaUpdate(BaseModel):
    descripcion: str | None = None


# ============================================================
# RESPONSE
# ============================================================
class TipoPersonaResponse(TipoPersonaBase):
    id: UUID
    descripcion: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None

    model_config = {"from_attributes": True}

# ============================================================
# LIST RESPONSE (versión ligera para listas paginadas)
# ============================================================
class TipoPersonaListResponse(BaseModel):
    id: UUID
    nombre: str
    descripcion: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}