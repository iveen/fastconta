"""Schemas para Categorías de Activos Fijos"""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# BASE
# ============================================================
class CategoriaActivoBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100, examples=["Vehículos"])
    descripcion: str | None = Field(None, examples=["Vehículos de transporte terrestre"])
    tasa_minima_anual: Decimal = Field(..., ge=0, le=100, examples=[Decimal("10.00")])
    tasa_maxima_anual: Decimal = Field(..., ge=0, le=100, examples=[Decimal("20.00")])
    vida_util_meses_default: int = Field(..., gt=0, examples=[60])
    codigo_prefijo: str = Field(..., min_length=1, max_length=10, examples=["VEH"])
    is_active: bool = True


class CategoriaActivoCreate(CategoriaActivoBase):
    pass


class CategoriaActivoUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    tasa_minima_anual: Decimal | None = None
    tasa_maxima_anual: Decimal | None = None
    vida_util_meses_default: int | None = None
    is_active: bool | None = None


# ============================================================
# RESPONSE
# ============================================================
class CategoriaActivoResponse(CategoriaActivoBase):
    id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None

    model_config = {"from_attributes": True}


class CategoriaActivoListResponse(BaseModel):
    id: UUID
    nombre: str
    codigo_prefijo: str
    tasa_minima_anual: Decimal
    tasa_maxima_anual: Decimal
    vida_util_meses_default: int
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}