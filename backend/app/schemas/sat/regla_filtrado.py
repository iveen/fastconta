# app/schemas/sat/regla_filtrado.py
"""Schemas para Reglas de Filtrado y Exclusiones de Casillas SAT"""
from pydantic import BaseModel, Field

# ============================================================
# TIPOS DE OPERACIÓN
# ============================================================
TIPOS_OPERACION = ["SUMA", "COUNT", "PROMEDIO", "MAX", "MIN"]


# ============================================================
# REGLA DE FILTRADO - BASE
# ============================================================
class ReglaFiltradoBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=255)
    descripcion: str | None = None
    criterios_json: dict = Field(
        ...,
        description="Criterios de filtrado en formato JSON",
        examples=[
            {"tipo_operacion": "Venta", "es_exento": False, "es_exportacion": False}
        ],
    )
    campo_factura: str = Field(
        ...,
        min_length=1,
        max_length=50,
        examples=["total_gravado_gtq", "total_iva_gtq", "total_exento_gtq"],
    )
    operacion: str = Field(..., min_length=1, max_length=20, examples=["SUMA"])
    orden: int = Field(0, ge=0)
    es_activa: bool = True


class ReglaFiltradoCreate(ReglaFiltradoBase):
    casilla_id: int  # ✅ BIGINT (era UUID)


class ReglaFiltradoUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    criterios_json: dict | None = None
    campo_factura: str | None = None
    operacion: str | None = None
    orden: int | None = None
    es_activa: bool | None = None


# ============================================================
# REGLA DE FILTRADO - RESPONSE
# ============================================================
class ReglaFiltradoResponse(ReglaFiltradoBase):
    id: int  # ✅ BIGINT (era UUID)
    casilla_id: int  # ✅ BIGINT (era UUID)
    created_at: str | None = None
    created_by: int | None = None  # ✅ BIGINT (era UUID)
    updated_at: str | None = None
    updated_by: int | None = None  # ✅ BIGINT (era UUID)

    model_config = {"from_attributes": True}


class ReglaFiltradoListResponse(BaseModel):
    id: int  # ✅ BIGINT (era UUID)
    nombre: str
    casilla_id: int  # ✅ BIGINT (era UUID)
    campo_factura: str
    operacion: str
    orden: int
    es_activa: bool

    model_config = {"from_attributes": True}


# ============================================================
# EXCLUSIÓN - BASE
# ============================================================
class ExclusionBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=255)
    descripcion: str | None = None
    criterios_exclusion_json: dict = Field(
        ...,
        description="Criterios de exclusión en formato JSON",
        examples=[{"tipo_documento": "FYDUCA", "pais_destino": "HND"}],
    )
    es_activa: bool = True


class ExclusionCreate(ExclusionBase):
    casilla_id: int  # ✅ BIGINT (era UUID)


class ExclusionUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    criterios_exclusion_json: dict | None = None
    es_activa: bool | None = None


# ============================================================
# EXCLUSIÓN - RESPONSE
# ============================================================
class ExclusionResponse(ExclusionBase):
    id: int  # ✅ BIGINT (era UUID)
    casilla_id: int  # ✅ BIGINT (era UUID)
    created_at: str | None = None
    created_by: int | None = None  # ✅ BIGINT (era UUID)
    updated_at: str | None = None
    updated_by: int | None = None  # ✅ BIGINT (era UUID)

    model_config = {"from_attributes": True}


class ExclusionListResponse(BaseModel):
    id: int  # ✅ BIGINT (era UUID)
    nombre: str
    casilla_id: int  # ✅ BIGINT (era UUID)
    es_activa: bool

    model_config = {"from_attributes": True}


# ============================================================
# CONFIGURACIÓN COMPLETA DE CASILLA
# ============================================================
class CasillaConfigResponse(BaseModel):
    """Respuesta completa con reglas y exclusiones de una casilla"""
    casilla_id: int  # ✅ BIGINT (era UUID)
    casilla_codigo: str
    casilla_nombre: str
    reglas: list[ReglaFiltradoResponse] = []
    exclusiones: list[ExclusionResponse] = []
    total_reglas: int = 0
    total_exclusiones: int = 0