"""Schemas para Tipos DTE"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# TIPO DTE - BASE
# ============================================================
class TipoDTEBase(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=10, examples=["FCAM"])
    descripcion: str = Field(..., min_length=1, max_length=100)
    requiere_complemento: bool = False
    es_factura: bool = True
    activo: bool = True


class TipoDTECreate(TipoDTEBase):
    pass


class TipoDTEUpdate(BaseModel):
    descripcion: str | None = None
    requiere_complemento: bool | None = None
    es_factura: bool | None = None
    activo: bool | None = None


# ============================================================
# TIPO DTE - RESPONSE (con auditoría completa)
# ============================================================
class TipoDTEResponse(TipoDTEBase):
    id: UUID
    # Auditoría completa (heredada de AuditableFull)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None

    model_config = {"from_attributes": True}


class TipoDTEListResponse(BaseModel):
    id: UUID
    codigo: str
    descripcion: str
    requiere_complemento: bool
    es_factura: bool
    activo: bool
    # Auditoría mínima para listados
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ============================================================
# IMPORT/EXPORT
# ============================================================
class TipoDTEImportItem(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=10)
    descripcion: str = Field(..., min_length=1, max_length=100)
    requiere_complemento: bool = False
    es_factura: bool = True


class TipoDTEImportRequest(BaseModel):
    items: list[TipoDTEImportItem]
    sobrescribir: bool = Field(
        False,
        description="Si es True, actualiza registros existentes. Si es False, solo crea nuevos.",
    )


class TipoDTEImportResult(BaseModel):
    creados: int = 0
    actualizados: int = 0
    omitidos: int = 0
    errores: list[str] = []


# ============================================================
# CONFIGURACIÓN RÉGIMEN-DTE
# ============================================================
class RegimenDteConfigCreate(BaseModel):
    regimen_id: UUID
    dte_id: UUID
    es_exclusivo: bool = False


class RegimenDteConfigResponse(BaseModel):
    id: UUID
    regimen_id: UUID
    dte_id: UUID
    es_exclusivo: bool
    # Datos enriquecidos de las relaciones
    regimen_codigo: str | None = None
    regimen_nombre: str | None = None
    dte_codigo: str | None = None
    dte_descripcion: str | None = None
    # Auditoría
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None

    model_config = {"from_attributes": True}


class RegimenDteConfigUpdate(BaseModel):
    es_exclusivo: bool | None = None


class RegimenDteBulkRequest(BaseModel):
    dte_ids: list[UUID] = Field(..., min_length=1)
    es_exclusivo: bool = False