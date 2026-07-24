"""Schemas para Catálogo de Impuestos"""
from datetime import datetime

from pydantic import BaseModel, Field


class ImpuestoBase(BaseModel):
    codigo: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=100)
    descripcion: str
    tasa_porcentaje: float | None = None
    tasa_fija_monto: float | None = 0.00
    limite_inferior: float | None = 0.00
    limite_superior: float | None = None
    frecuencia_pago: str = Field(..., max_length=20)
    frecuencia_liquidacion: str = Field(..., max_length=20)
    es_acreditable: bool = False
    requiere_autorizacion_sat: bool = False


class ImpuestoCreate(ImpuestoBase):
    pass


class ImpuestoUpdate(BaseModel):
    codigo: str | None = Field(None, max_length=20)
    nombre: str | None = Field(None, max_length=100)
    descripcion: str | None = None
    tasa_porcentaje: float | None = None
    tasa_fija_monto: float | None = None
    limite_inferior: float | None = None
    limite_superior: float | None = None
    frecuencia_pago: str | None = Field(None, max_length=20)
    frecuencia_liquidacion: str | None = Field(None, max_length=20)
    es_acreditable: bool | None = None
    requiere_autorizacion_sat: bool | None = None


class ImpuestoResponse(ImpuestoBase):
    id: int  # ✅ BIGINT
    public_id: str  # ✅ UUID como string
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None
    created_by: int | None = None  # ✅ BIGINT
    updated_by: int | None = None  # ✅ BIGINT

    model_config = {"from_attributes": True}


class ImpuestoListResponse(BaseModel):
    id: int  # ✅ BIGINT
    public_id: str  # ✅ UUID como string
    codigo: str
    nombre: str
    tasa_porcentaje: float | None = None
    es_acreditable: bool
    is_active: bool

    model_config = {"from_attributes": True}