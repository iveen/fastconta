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
    is_active: bool = True


class ActividadEconomicaCreate(ActividadEconomicaBase):
    pass


class ActividadEconomicaUpdate(BaseModel):
    nombre_actividad: str | None = None
    seccion: str | None = None
    is_active: bool | None = None


# ============================================================
# RESPONSE
# ============================================================
class ActividadEconomicaResponse(ActividadEconomicaBase):
    id: int  # ✅ BIGINT (era UUID)
    public_id: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: int | None = None
    updated_by: int | None = None

    model_config = {"from_attributes": True}


class ActividadEconomicaListResponse(BaseModel):
    id: int  # ✅ BIGINT (era UUID)
    public_id: UUID | None = None
    codigo_sat: str
    nombre_actividad: str
    seccion: str | None = None
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}