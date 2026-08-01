"""Schemas para Declaraciones SAT (2237)"""
from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field


# ============================================================
# REQUESTS
# ============================================================
class GenerarSombraRequest(BaseModel):
    empresa_id: int  # ✅ BIGINT
    anio: int = Field(..., ge=2020, le=2030)
    mes: int = Field(..., ge=1, le=12)
    codigo_formulario: str = "SAT-2237"


class AjusteManualRequest(BaseModel):
    base_imponible: Decimal | None = None
    monto_impuesto: Decimal | None = None
    motivo_ajuste: str = Field(
        ...,
        min_length=5,
        description="Obligatorio al hacer un ajuste manual",
    )


# ============================================================
# RESPONSES
# ============================================================
class CasillaDetalleOut(BaseModel):
    """Detalle de una casilla en la declaración"""
    casilla_codigo: str
    casilla_nombre: str
    seccion: str
    tipo_casilla: str
    base_imponible: Decimal
    monto_impuesto: Decimal
    es_ajuste_manual: bool
    motivo_ajuste: str | None = None

    model_config = {"from_attributes": True}


class DeclaracionSombraOut(BaseModel):
    """Respuesta completa de una declaración sombra"""
    id: int  # ✅ BIGINT
    empresa_id: int  # ✅ BIGINT
    formulario_codigo: str
    anio: int
    mes: int
    estado: str
    total_debito_fiscal: Decimal
    total_credito_fiscal: Decimal
    impuesto_determinado: Decimal  # ✅ Agregado (útil para el frontend)
    remanente_periodo_anterior: Decimal  # ✅ Agregado
    impuesto_a_pagar: Decimal
    remanente_siguiente_periodo: Decimal
    detalles: List[CasillaDetalleOut]
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
