# app/schemas/configuracion_fiscal/formulario.py
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.sat.seccion import SeccionFormularioResponse


class FormularioSatBase(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=20, examples=["SAT-2237"])
    version: str = Field(..., min_length=1, max_length=10, examples=["1.0"])
    nombre: str = Field(..., min_length=1, max_length=255)
    descripcion: str | None = None
    fecha_vigencia_desde: date
    fecha_vigencia_hasta: date | None = None
    es_version_activa: bool = True
    editable: bool = True


class FormularioSatCreate(FormularioSatBase):
    pass


class FormularioSatUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    fecha_vigencia_hasta: date | None = None
    es_version_activa: bool | None = None
    editable: bool | None = None


class FormularioSatResponse(FormularioSatBase):
    id: int  # ✅ BIGINT (era UUID)
    formulario_padre_id: int | None = None  # ✅ BIGINT (era UUID)
    created_at: datetime | None = None
    created_by: int | None = None  # ✅ BIGINT (era UUID)
    updated_at: datetime | None = None
    updated_by: int | None = None  # ✅ BIGINT (era UUID)

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


class FormularioSatDuplicarRequest(BaseModel):
    """Request para crear nueva versión desde una existente"""
    nueva_version: str = Field(..., min_length=1, max_length=10, examples=["2.0"])
    fecha_vigencia_desde: date
    copiar_casillas: bool = True
    copiar_secciones: bool = True
    copiar_reglas_filtrado: bool = True
    copiar_exclusiones: bool = True


class FormularioSatListResponse(BaseModel):
    id: int  # ✅ BIGINT (era UUID)
    codigo: str
    version: str
    nombre: str
    fecha_vigencia_desde: date
    fecha_vigencia_hasta: date | None = None
    es_version_activa: bool
    total_secciones: int = 0
    total_casillas: int = 0

    model_config = {"from_attributes": True}