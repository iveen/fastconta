"""Schemas para Empresas"""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer


class EmpresaSimple(BaseModel):
    """Schema ligero para dropdowns (sin relaciones)"""
    id: UUID
    nombre: str
    nit: str
    nombre_comercial: str | None = None
    is_active: bool = True

    model_config = {"from_attributes": True}


class EmpresaCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=255)
    nit: str = Field(..., min_length=7, max_length=20)
    razon_social: str | None = None
    nombre_comercial: str | None = None
    fecha_constitucion: date | None = None
    regimen_fiscal_id: UUID | None = None
    tipo_persona_id: UUID | None = None
    actividad_economica_id: UUID | None = None
    direccion: str | None = None


class EmpresaUpdate(BaseModel):
    nombre: str | None = None
    nit: str | None = None
    razon_social: str | None = None
    nombre_comercial: str | None = None
    fecha_constitucion: date | None = None
    regimen_fiscal_id: UUID | None = None
    tipo_persona_id: UUID | None = None
    actividad_economica_id: UUID | None = None
    direccion: str | None = None
    cuenta_utilidad_periodo_id: UUID | None = None
    cuenta_utilidades_acumuladas_id: UUID | None = None
    is_active: bool | None = None


class EmpresaOut(BaseModel):
    id: UUID
    nombre: str
    nit: str
    razon_social: str | None = None
    nombre_comercial: str | None = None
    fecha_constitucion: date | None = None
    regimen_fiscal_id: UUID | None = None
    tipo_persona_id: UUID | None = None
    actividad_economica_id: UUID | None = None
    direccion: str | None = None
    cuenta_utilidad_periodo_id: UUID | None = None
    cuenta_utilidades_acumuladas_id: UUID | None = None
    is_active: bool
    
    # ✅ CORREGIDO: Aceptar datetime y convertir a string
    created_at: datetime | None = None
    
    @field_serializer('created_at')
    def serialize_created_at(self, dt: datetime | None) -> str | None:
        if dt is None:
            return None
        return dt.isoformat()

    model_config = {"from_attributes": True}

class NitValidarRequest(BaseModel):
    nit: str