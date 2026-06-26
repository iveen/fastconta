"""Schemas para Catálogo de Monedas"""

from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# BASE
# ============================================================
class CatalogoMonedaBase(BaseModel):
    codigo_banguat: str = Field(
        ...,
        min_length=1,
        max_length=5,
        examples=["001"],
        description="Código según Banco de Guatemala",
    )
    codigo_iso: str = Field(
        ...,
        min_length=3,
        max_length=3,
        examples=["GTQ"],
        description="Código ISO 4217",
    )
    nombre: str = Field(..., min_length=1, max_length=50, examples=["Quetzal"])
    simbolo: str | None = Field(None, max_length=5, examples=["Q"])
    decimales: int = Field(2, ge=0, le=6, description="Cantidad de decimales")
    activo: bool = True


class CatalogoMonedaCreate(CatalogoMonedaBase):
    pass


class CatalogoMonedaUpdate(BaseModel):
    nombre: str | None = None
    simbolo: str | None = None
    decimales: int | None = None
    activo: bool | None = None


# ============================================================
# RESPONSE
# ============================================================
class CatalogoMonedaResponse(CatalogoMonedaBase):
    id: UUID
    created_at: str | None = None
    updated_at: str | None = None

    model_config = {"from_attributes": True}


class CatalogoMonedaListResponse(BaseModel):
    id: UUID
    codigo_banguat: str
    codigo_iso: str
    nombre: str
    simbolo: str | None = None
    decimales: int
    activo: bool

    model_config = {"from_attributes": True}


# ============================================================
# IMPORT/EXPORT
# ============================================================
class CatalogoMonedaImportItem(BaseModel):
    codigo_banguat: str = Field(..., min_length=1, max_length=5)
    codigo_iso: str = Field(..., min_length=3, max_length=3)
    nombre: str = Field(..., min_length=1, max_length=50)
    simbolo: str | None = None
    decimales: int = Field(2, ge=0, le=6)


class CatalogoMonedaImportResult(BaseModel):
    """Resultado de importación"""
    creados: int = 0
    actualizados: int = 0
    omitidos: int = 0
    errores: list[str] = []


class CatalogoMonedaBulkRequest(BaseModel):
    """Request para importación masiva"""
    items: list[CatalogoMonedaImportItem]
    sobrescribir: bool = Field(
        False,
        description="Si es True, actualiza registros existentes",
    )