"""Schemas para Casillas SAT"""

from uuid import UUID

from pydantic import BaseModel, Field

# ============================================================
# TIPOS DE CASILLA (enum-like)
# ============================================================
TIPOS_CASILLA = [
    "BASE_IMPONIBLE",
    "DEBITO_FISCAL",
    "CREDITO_FISCAL",
    "REFERENCIA",
    "CALCULADO",
    "REMANENTE",
    "AJUSTE",
    "CONTEO",
    "MANUAL",
]

NATURALEZAS_CASILLA = [
    "SUMA",
    "RESTA",
    "PORCENTAJE",
    "MANUAL",
    "CONTEO",
]


# ============================================================
# BASE
# ============================================================
class CasillaSatBase(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=50, examples=["3.1"])
    codigo_visual: str | None = Field(None, max_length=20, examples=["3.1"])
    nombre: str = Field(..., min_length=1, max_length=255)
    descripcion: str | None = None
    orden_seccion: int = Field(0, ge=0)
    tipo_casilla: str = Field(..., min_length=1, max_length=30)
    naturaleza: str | None = Field(None, max_length=20)
    formula_calculo: str | None = None
    porcentaje_aplicable: float | None = Field(None, ge=0, le=100)
    campo_origen_factura: str | None = Field(None, max_length=50)
    es_editable: bool = False
    requiere_justificacion: bool = False
    es_visible_usuario: bool = True


class CasillaSatCreate(CasillaSatBase):
    seccion_id: UUID


class CasillaSatUpdate(BaseModel):
    codigo_visual: str | None = None
    nombre: str | None = None
    descripcion: str | None = None
    orden_seccion: int | None = None
    tipo_casilla: str | None = None
    naturaleza: str | None = None
    formula_calculo: str | None = None
    porcentaje_aplicable: float | None = None
    campo_origen_factura: str | None = None
    es_editable: bool | None = None
    requiere_justificacion: bool | None = None
    es_visible_usuario: bool | None = None


# ============================================================
# RESPONSE
# ============================================================
class CasillaSatResponse(CasillaSatBase):
    id: UUID
    seccion_id: UUID | None = None
    formulario_id: UUID | None = None  # Via property
    created_at: str | None = None
    created_by: UUID | None = None
    updated_at: str | None = None
    updated_by: UUID | None = None

    model_config = {"from_attributes": True}


class CasillaSatDetail(CasillaSatResponse):
    """Respuesta detallada con reglas y exclusiones"""
    total_reglas: int = 0
    total_exclusiones: int = 0


class CasillaSatListResponse(BaseModel):
    id: UUID
    codigo: str
    codigo_visual: str | None = None
    nombre: str
    tipo_casilla: str
    naturaleza: str | None = None
    orden_seccion: int
    es_editable: bool
    es_visible_usuario: bool
    formula_calculo: str | None = None

    model_config = {"from_attributes": True}


# ============================================================
# DUPLICAR CASILLA
# ============================================================
class CasillaSatDuplicarRequest(BaseModel):
    """Request para duplicar una casilla"""
    nuevo_codigo: str = Field(..., min_length=1, max_length=50)
    nuevo_nombre: str | None = Field(None, min_length=1, max_length=255)
    copiar_reglas: bool = True
    copiar_exclusiones: bool = True