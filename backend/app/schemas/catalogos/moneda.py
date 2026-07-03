"""Schemas para Catálogo de Monedas"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# BASE
# ============================================================
class MonedaBase(BaseModel):
    codigo_banguat: str = Field(..., min_length=1, max_length=5, examples=["001"])
    codigo_iso: str = Field(..., min_length=3, max_length=3, examples=["GTQ"])
    nombre: str = Field(..., min_length=1, max_length=50, examples=["Quetzal"])
    simbolo: str | None = Field(None, max_length=5, examples=["Q"])
    decimales: int = Field(default=2, ge=0, le=10)
    activo: bool = True


class MonedaCreate(MonedaBase):
    pass


class MonedaUpdate(BaseModel):
    nombre: str | None = None
    simbolo: str | None = None
    decimales: int | None = None
    activo: bool | None = None


# ============================================================
# RESPONSE
# ============================================================
class MonedaResponse(MonedaBase):
    id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None

    model_config = {"from_attributes": True}


class MonedaListResponse(BaseModel):
    id: UUID
    codigo_banguat: str
    codigo_iso: str
    nombre: str
    simbolo: str | None = None
    activo: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}