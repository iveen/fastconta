"""Schemas para Tipos DTE"""

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
# TIPO DTE - RESPONSE
# ============================================================
class TipoDTEResponse(TipoDTEBase):
    id: UUID
    created_at: str | None = None
    updated_at: str | None = None

    model_config = {"from_attributes": True}


class TipoDTEListResponse(BaseModel):
    id: UUID
    codigo: str
    descripcion: str
    requiere_complemento: bool
    es_factura: bool
    activo: bool

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
    """Request para importación masiva"""
    items: list[TipoDTEImportItem]
    sobrescribir: bool = Field(
        False,
        description="Si es True, actualiza registros existentes. Si es False, solo crea nuevos.",
    )


class TipoDTEImportResult(BaseModel):
    """Resultado de importación"""
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
    regimen_codigo: str | None = None
    regimen_nombre: str | None = None
    dte_codigo: str | None = None
    dte_descripcion: str | None = None

    model_config = {"from_attributes": True}


class RegimenDteConfigUpdate(BaseModel):
    es_exclusivo: bool | None = None


class RegimenDteBulkRequest(BaseModel):
    """Request para asociar/desasociar múltiples DTE a un régimen"""
    dte_ids: list[UUID] = Field(..., min_length=1)
    es_exclusivo: bool = False