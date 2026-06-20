"""Schemas para Formulario SAT con versionado"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.configuracion_fiscal.seccion import SeccionFormularioResponse


# ============================================================
# BASE
# ============================================================
class FormularioSatBase(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=20, examples=["SAT-2237"])
    version: str = Field(..., min_length=1, max_length=10, examples=["1.0"])
    nombre: str = Field(..., min_length=1, max_length=255)
    descripcion: str | None = None
    fecha_vigencia_desde: date
    fecha_vigencia_hasta: date | None = None
    es_version_activa: bool = True


class FormularioSatCreate(FormularioSatBase):
    pass


class FormularioSatUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    fecha_vigencia_hasta: date | None = None
    es_version_activa: bool | None = None


# ============================================================
# RESPONSE
# ============================================================
class FormularioSatResponse(FormularioSatBase):
    id: UUID
    formulario_padre_id: UUID | None = None
    created_at: datetime | None = None
    created_by: UUID | None = None
    updated_at: datetime | None = None
    updated_by: UUID | None = None

    model_config = {"from_attributes": True}


class FormularioSatDetail(FormularioSatResponse):
    """Respuesta detallada con secciones y casillas"""
    secciones: list["SeccionFormularioResponse"] = []
    total_secciones: int = 0
    total_casillas: int = 0


class FormularioSatHistorial(BaseModel):
    """Respuesta para endpoint de historial de versiones"""
    codigo: str
    versiones: list[FormularioSatResponse]
    version_actual: FormularioSatResponse | None = None
    total_versiones: int


# ============================================================
# DUPLICAR VERSIÓN
# ============================================================
class FormularioSatDuplicarRequest(BaseModel):
    """Request para crear nueva versión desde una existente"""
    nueva_version: str = Field(..., min_length=1, max_length=10, examples=["2.0"])
    fecha_vigencia_desde: date
    copiar_casillas: bool = True
    copiar_secciones: bool = True
    copiar_reglas_filtrado: bool = True
    copiar_exclusiones: bool = True


# ============================================================
# LISTA RESUMEN
# ============================================================
class FormularioSatListResponse(BaseModel):
    id: UUID
    codigo: str
    version: str
    nombre: str
    fecha_vigencia_desde: date
    fecha_vigencia_hasta: date | None = None
    es_version_activa: bool
    total_secciones: int = 0
    total_casillas: int = 0

    model_config = {"from_attributes": True}