# app/schemas/balances.py
from datetime import date
from decimal import Decimal
from typing import List

from pydantic import BaseModel, ConfigDict


class FilaBalance(BaseModel):
    cuenta_id: int  # ✅ BIGINT
    codigo: str
    nombre: str
    tipo: str
    naturaleza: str
    sum_debe: Decimal
    sum_haber: Decimal
    saldo: Decimal
    model_config = ConfigDict(from_attributes=True)


class BalanceComprobacionResponse(BaseModel):
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    filas: List[FilaBalance]


class EstadoResultadosResponse(BaseModel):
    empresa_id: int  # ✅ BIGINT
    empresa_nombre: str
    fecha_inicio: date
    fecha_fin: date
    ingresos: List[FilaBalance]
    total_ingresos: Decimal
    gastos: List[FilaBalance]
    total_gastos: Decimal
    utilidad_neta: Decimal


class BalanceGeneralResponse(BaseModel):
    empresa_id: int  # ✅ BIGINT
    empresa_nombre: str
    fecha: date
    activos: List[FilaBalance]
    total_activos: Decimal
    pasivos: List[FilaBalance]
    total_pasivos: Decimal
    patrimonio: List[FilaBalance]
    total_patrimonio: Decimal
    utilidad_ejercicio: Decimal