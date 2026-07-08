"""Schemas para Domicilios de Empresas"""
from uuid import UUID

from pydantic import BaseModel, Field

# ============================================================
# SCHEMAS DE RESPUESTA PARA CATÁLOGOS (Geografía)
# ============================================================

class DepartamentoOut(BaseModel):
    id: int  # ✅ BIGINT
    public_id: UUID  # ✅ UUID público
    codigo_iso: str
    nombre: str

    model_config = {"from_attributes": True}


class MunicipioOut(BaseModel):
    id: int  # ✅ BIGINT
    public_id: UUID  # ✅ UUID público  
    nombre: str
    departamento_id: UUID

    model_config = {"from_attributes": True}


class TipoDomicilioOut(BaseModel):
    id: int  # ✅ BIGINT
    public_id: UUID  # ✅ UUID público
    nombre: str

    model_config = {"from_attributes": True}


# ============================================================
# SCHEMAS PARA DOMICILIO
# ============================================================

class DomicilioCreate(BaseModel):
    tipo_domicilio_id: int
    departamento_id: int
    municipio_id: int
    direccion_exacta: str = Field(..., min_length=1, max_length=255)
    zona: str | None = Field(None, max_length=10)
    codigo_postal: str | None = Field(None, max_length=10)


class DomicilioUpdate(BaseModel):
    tipo_domicilio_id: int | None = None
    departamento_id: int | None = None
    municipio_id: int | None = None
    direccion_exacta: str | None = Field(None, min_length=1, max_length=255)
    zona: str | None = Field(None, max_length=10)
    codigo_postal: str | None = Field(None, max_length=10)


class DomicilioOut(BaseModel):
    id: int  # ✅ BIGINT
    empresa_id: int  # ✅ BIGINT
    tipo_domicilio_id: int  # ✅ BIGINT
    departamento_id: int  # ✅ BIGINT
    municipio_id: int  # ✅ BIGINT
    direccion_exacta: str
    zona: str | None = None
    codigo_postal: str | None = None

    # Relaciones resueltas (se llenan manualmente en el endpoint)
    tipo_domicilio_nombre: str | None = None
    departamento_nombre: str | None = None
    municipio_nombre: str | None = None

    model_config = {"from_attributes": True}
