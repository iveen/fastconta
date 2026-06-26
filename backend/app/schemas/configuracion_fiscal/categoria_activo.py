"""Schemas para Categorías de Activos Fijos"""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


# ============================================================
# BASE
# ============================================================
class CategoriaActivoFijoBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100, examples=["Vehículos"])
    descripcion: str | None = None
    tasa_minima_anual: Decimal = Field(
        ...,
        ge=0,
        le=100,
        examples=[20.00],
        description="Tasa mínima de depreciación anual (%)",
    )
    tasa_maxima_anual: Decimal = Field(
        ...,
        ge=0,
        le=100,
        examples=[20.00],
        description="Tasa máxima de depreciación anual (%)",
    )
    vida_util_meses_default: int = Field(
        ...,
        gt=0,
        examples=[60],
        description="Vida útil en meses según SAT",
    )
    codigo_prefijo: str = Field(
        ...,
        min_length=1,
        max_length=10,
        examples=["VEH"],
        description="Prefijo para código interno del activo",
    )


class CategoriaActivoFijoCreate(CategoriaActivoFijoBase):
    pass


class CategoriaActivoFijoUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    tasa_minima_anual: Decimal | None = None
    tasa_maxima_anual: Decimal | None = None
    vida_util_meses_default: int | None = None
    codigo_prefijo: str | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validar_tasas(self):
        """Valida que tasa_maxima >= tasa_minima"""
        if (
            self.tasa_minima_anual is not None
            and self.tasa_maxima_anual is not None
            and self.tasa_maxima_anual < self.tasa_minima_anual
        ):
            raise ValueError(
                "La tasa máxima anual debe ser mayor o igual a la tasa mínima anual"
            )
        return self


# ============================================================
# RESPONSE
# ============================================================
class CategoriaActivoFijoResponse(CategoriaActivoFijoBase):
    id: UUID
    is_active: bool
    created_at: str | None = None

    model_config = {"from_attributes": True}


class CategoriaActivoFijoListResponse(BaseModel):
    id: UUID
    nombre: str
    codigo_prefijo: str
    tasa_minima_anual: Decimal
    tasa_maxima_anual: Decimal
    vida_util_meses_default: int
    is_active: bool

    model_config = {"from_attributes": True}


# ============================================================
# IMPORT/EXPORT
# ============================================================
class CategoriaActivoImportItem(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    descripcion: str | None = None
    tasa_minima_anual: Decimal = Field(..., ge=0, le=100)
    tasa_maxima_anual: Decimal = Field(..., ge=0, le=100)
    vida_util_meses_default: int = Field(..., gt=0)
    codigo_prefijo: str = Field(..., min_length=1, max_length=10)


class CategoriaActivoImportResult(BaseModel):
    """Resultado de importación"""
    creados: int = 0
    actualizados: int = 0
    omitidos: int = 0
    errores: list[str] = []


class CategoriaActivoBulkRequest(BaseModel):
    """Request para importación masiva"""
    items: list[CategoriaActivoImportItem]
    sobrescribir: bool = Field(
        False,
        description="Si es True, actualiza registros existentes",
    )