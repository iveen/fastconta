# app/schemas/balances.py
from pydantic import BaseModel
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

class MovimientoCuenta(BaseModel):
    fecha: date
    partida_id: UUID
    descripcion_partida: str
    tipo_movimiento: str  # "debe" o "haber"
    monto: Decimal

class LibroMayorResponse(BaseModel):
    cuenta_id: UUID
    cuenta_codigo: str
    cuenta_nombre: str
    naturaleza: str
    movimientos: List[MovimientoCuenta]
    saldo_actual: Decimal

class FilaBalance(BaseModel):
    cuenta_id: UUID
    codigo: str
    nombre: str
    tipo: str
    naturaleza: str
    sum_debe: Decimal
    sum_haber: Decimal
    saldo: Decimal

class BalanceComprobacionResponse(BaseModel):
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    filas: List[FilaBalance]