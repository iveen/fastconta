"""Schemas para Secciones de Formulario SAT"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.configuracion_fiscal.casilla import CasillaSatResponse


# ============================================================
# BASE
# ============================================================
class SeccionFormularioBase(BaseModel):
    numero_seccion: str = Field(..., min_length=1, max_length=10, examples=["3"])
    titulo: str = Field(..., min_length=1, max_length=255)
    descripcion: str | None = None
    orden: int = Field(..., ge=0)
    tipo_seccion: str = Field(
        ...,
        min_length=1,
        max_length=30,
        examples=[
            "IDENTIFICACION",
            "PERIODO",
            "DEBITO_FISCAL",
            "CREDITO_FISCAL",
            "EXPORTACIONES",
            "DETERMINACION",
            "INFORMATIVA",
            "RECTIFICACION",
            "ACCESORIOS",
        ],
    )
    es_obligatoria: bool = True
    requiere_exportador: bool = False


class SeccionFormularioCreate(SeccionFormularioBase):
    formulario_id: UUID


class SeccionFormularioUpdate(BaseModel):
    titulo: str | None = None
    descripcion: str | None = None
    orden: int | None = None
    tipo_seccion: str | None = None
    es_obligatoria: bool | None = None
    requiere_exportador: bool | None = None


# ============================================================
# RESPONSE
# ============================================================
class SeccionFormularioResponse(SeccionFormularioBase):
    id: UUID
    formulario_id: UUID
    created_at: datetime | None = None
    created_by: UUID | None = None
    updated_at: datetime | None = None
    updated_by: UUID | None = None
    casillas: list["CasillaSatResponse"]
    total_casillas: int = 0

    model_config = {"from_attributes": True}


class SeccionFormularioDetail(SeccionFormularioResponse):
    """Respuesta detallada con casillas"""
    total_casillas: int = 0


class SeccionFormularioListResponse(BaseModel):
    id: UUID
    numero_seccion: str
    titulo: str
    tipo_seccion: str
    orden: int
    es_obligatoria: bool
    requiere_exportador: bool
    total_casillas: int = 0

    model_config = {"from_attributes": True}


# ============================================================
# REORDENAR
# ============================================================
class SeccionReordenarRequest(BaseModel):
    """Request para reordenar secciones"""
    orden_secciones: list[UUID] = Field(
        ...,
        description="Lista de IDs de secciones en el nuevo orden",
        examples=[["uuid-1", "uuid-2", "uuid-3"]],
    )