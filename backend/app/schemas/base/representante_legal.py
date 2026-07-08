"""Schemas para Representantes Legales de Empresas"""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer

# ============================================================
# SCHEMAS PARA REPRESENTANTE LEGAL
# ============================================================

class RepresentanteLegalCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=255)
    tipo_identificacion: str = Field(..., min_length=1, max_length=20, examples=["DPI", "NIT", "Pasaporte"])
    numero_identificacion: str = Field(..., min_length=1, max_length=20)
    fecha_nombramiento: date
    email: str | None = Field(None, max_length=255)


class RepresentanteLegalUpdate(BaseModel):
    nombre: str | None = Field(None, min_length=1, max_length=255)
    tipo_identificacion: str | None = Field(None, min_length=1, max_length=20)
    numero_identificacion: str | None = Field(None, min_length=1, max_length=20)
    fecha_nombramiento: date | None = None
    email: str | None = Field(None, max_length=255)
    es_activo: bool | None = None


class RepresentanteLegalOut(BaseModel):
    id: int  # ✅ BIGINT
    public_id: UUID  # ✅ UUID público
    empresa_id: int  # ✅ BIGINT
    nombre: str
    tipo_identificacion: str
    numero_identificacion: str
    fecha_nombramiento: date
    email: str | None = None
    is_active: bool
    created_at: datetime | None = None

    @field_serializer('created_at')
    def serialize_created_at(self, dt: datetime | None) -> str | None:
        if dt is None:
            return None
        return dt.isoformat()

    model_config = {"from_attributes": True}