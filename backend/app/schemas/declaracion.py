from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field


class GenerarSombraRequest(BaseModel):
    empresa_id: UUID
    anio: int = Field(..., ge=2020, le=2030)
    mes: int = Field(..., ge=1, le=12)
    codigo_formulario: str = "SAT-2237"

class AjusteManualRequest(BaseModel):
    base_imponible: Decimal | None = None
    monto_impuesto: Decimal | None = None
    motivo_ajuste: str = Field(..., min_length=5, description="Obligatorio al hacer un ajuste manual")

class CasillaDetalleOut(BaseModel):
    casilla_codigo: str
    casilla_nombre: str
    seccion: str
    tipo_casilla: str
    base_imponible: Decimal
    monto_impuesto: Decimal
    es_ajuste_manual: bool
    motivo_ajuste: str | None = None

    class Config:
        from_attributes = True

class DeclaracionSombraOut(BaseModel):
    id: UUID
    empresa_id: UUID
    formulario_codigo: str
    anio: int
    mes: int
    estado: str
    total_debito_fiscal: Decimal
    total_credito_fiscal: Decimal
    impuesto_a_pagar: Decimal
    remanente_siguiente_periodo: Decimal
    detalles: List[CasillaDetalleOut]
    created_at: datetime

    class Config:
        from_attributes = True