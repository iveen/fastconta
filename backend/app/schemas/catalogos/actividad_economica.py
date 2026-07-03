"""Schemas para Actividades Económicas SAT"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# BASE
# ============================================================
class ActividadEconomicaBase(BaseModel):
    codigo_sat: str = Field(..., min_length=1, max_length=20, examples=["01101"])
    nombre_actividad: str = Field(..., min_length=1, max_length=255)
    seccion: str | None = Field(None, max_length=255)
    activa: bool = True


class ActividadEconomicaCreate(ActividadEconomicaBase):
    pass


class ActividadEconomicaUpdate(BaseModel):
    nombre_actividad: str | None = None
    seccion: str | None = None
    activa: bool | None = None


# ============================================================
# RESPONSE
# ============================================================
class ActividadEconomicaResponse(ActividadEconomicaBase):
    id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None

    model_config = {"from_attributes": True}


class ActividadEconomicaListResponse(BaseModel):
    id: UUID
    codigo_sat: str
    nombre_actividad: str
    seccion: str | None = None
    activa: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}