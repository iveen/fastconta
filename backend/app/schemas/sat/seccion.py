# app/schemas/configuracion_fiscal/seccion.py
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.sat.casilla import CasillaSatResponse


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
    es_automatica: bool = False


class SeccionFormularioCreate(SeccionFormularioBase):
    formulario_id: int  # ✅ BIGINT (era UUID)


class SeccionFormularioUpdate(BaseModel):
    titulo: str | None = None
    descripcion: str | None = None
    orden: int | None = None
    tipo_seccion: str | None = None
    es_obligatoria: bool | None = None
    requiere_exportador: bool | None = None


class SeccionFormularioResponse(SeccionFormularioBase):
    id: int  # ✅ BIGINT (era UUID)
    formulario_id: int  # ✅ BIGINT (era UUID)
    created_at: datetime | None = None
    created_by: int | None = None  # ✅ BIGINT (era UUID)
    updated_at: datetime | None = None
    updated_by: int | None = None  # ✅ BIGINT (era UUID)
    casillas: list[CasillaSatResponse] = []
    total_casillas: int = 0

    model_config = {"from_attributes": True}


class SeccionFormularioDetail(SeccionFormularioResponse):
    """Respuesta detallada con casillas"""
    pass


class SeccionFormularioListResponse(BaseModel):
    id: int  # ✅ BIGINT (era UUID)
    numero_seccion: str
    titulo: str
    tipo_seccion: str
    orden: int
    es_obligatoria: bool
    requiere_exportador: bool
    total_casillas: int = 0

    model_config = {"from_attributes": True}


class SeccionReordenarRequest(BaseModel):
    """Request para reordenar secciones"""
    orden_secciones: list[int] = Field(  # ✅ BIGINT (era list[UUID])
        ...,
        description="Lista de IDs de secciones en el nuevo orden",
        examples=[[1, 2, 3]],
    )