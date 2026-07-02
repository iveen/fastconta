"""Schemas para Representantes Legales de Empresas"""
from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

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
    id: UUID
    empresa_id: UUID
    nombre: str
    tipo_identificacion: str
    numero_identificacion: str
    fecha_nombramiento: date
    email: str | None = None
    es_activo: bool
    created_at: str | None = None

    model_config = {"from_attributes": True}