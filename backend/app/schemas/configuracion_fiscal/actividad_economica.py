"""Schemas para Actividades Económicas SAT"""

from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# BASE
# ============================================================
class ActividadEconomicaBase(BaseModel):
    codigo_sat: str = Field(..., min_length=1, max_length=20, examples=["01111"])
    nombre_actividad: str = Field(..., min_length=1, max_length=255)
    seccion: str | None = Field(None, max_length=255)
    activa: bool = True


class ActividadEconomicaCreate(ActividadEconomicaBase):
    pass


class ActividadEconomicaUpdate(BaseModel):
    nombre_actividad: str | None = None
    seccion: str | None = None
    activa: bool | None = None


# ============================================================
# RESPONSE
# ============================================================
class ActividadEconomicaResponse(ActividadEconomicaBase):
    id: UUID
    created_at: str | None = None

    model_config = {"from_attributes": True}


class ActividadEconomicaListResponse(BaseModel):
    id: UUID
    codigo_sat: str
    nombre_actividad: str
    seccion: str | None = None
    activa: bool

    model_config = {"from_attributes": True}


# ============================================================
# IMPORT/EXPORT
# ============================================================
class ActividadEconomicaImportItem(BaseModel):
    codigo_sat: str = Field(..., min_length=1, max_length=20)
    nombre_actividad: str = Field(..., min_length=1, max_length=255)
    seccion: str | None = None


class ActividadEconomicaImportResult(BaseModel):
    """Resultado de importación"""
    creados: int = 0
    actualizados: int = 0
    omitidos: int = 0
    errores: list[str] = []


class ActividadEconomicaBulkRequest(BaseModel):
    """Request para importación masiva"""
    items: list[ActividadEconomicaImportItem]
    sobrescribir: bool = Field(
        False,
        description="Si es True, actualiza registros existentes. Si es False, solo crea nuevos.",
    )