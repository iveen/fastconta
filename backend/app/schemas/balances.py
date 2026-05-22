# app/schemas/balances.py
from pydantic import BaseModel
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

class MovimientoCuenta(BaseModel):
    fecha: date
    partida_id: UUID
    numero_poliza: Optional[str] = None  # <-- nuevo
    descripcion_partida: str
    tipo_movimiento: str
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

class EstadoResultadosResponse(BaseModel):
    empresa_id: UUID
    empresa_nombre: str
    fecha_inicio: date
    fecha_fin: date
    ingresos: List[FilaBalance]
    total_ingresos: Decimal
    gastos: List[FilaBalance]
    total_gastos: Decimal
    utilidad_neta: Decimal  # Puede ser negativo si es pérdida