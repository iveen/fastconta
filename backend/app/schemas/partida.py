

from datetime import date, datetime
from decimal import Decimal
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class DetallePartidaCreate(BaseModel):
    cuenta_id: UUID
    tipo_movimiento: str = Field(..., description="Debe ser 'debe' o 'haber'")
    monto: Decimal = Field(..., gt=0, description="El monto debe ser mayor a 0")

    @model_validator(mode='after')
    def validar_tipo_movimiento(self):
        if self.tipo_movimiento.lower() not in ['debe', 'haber']:
            raise ValueError("El tipo de movimiento debe ser 'debe' o 'haber' (en minúsculas).")
        return self


class PartidaCreate(BaseModel):
    fecha: date
    descripcion: str
    numero_poliza: str | None = None
    detalles: List[DetallePartidaCreate]

    @model_validator(mode='after')
    def validar_partida_cuadrada(self):
        if not self.detalles or len(self.detalles) < 2:
            raise ValueError("Una partida contable debe tener al menos 2 líneas de detalle.")
        
        # Calcular totales
        total_debe = sum(d.monto for d in self.detalles if d.tipo_movimiento.lower() == 'debe')
        total_haber = sum(d.monto for d in self.detalles if d.tipo_movimiento.lower() == 'haber')
        
        # Verificar equilibrio
        if total_debe != total_haber:
            diferencia = abs(total_debe - total_haber)
            raise ValueError(
                f"La partida no está cuadrada. "
                f"Total DEBE: {total_debe:,.2f} | Total HABER: {total_haber:,.2f}. "
                f"Diferencia: {diferencia:,.2f}. "
                f"Por favor, revisa que los montos y los tipos de movimiento ('debe'/'haber') de cada línea sean correctos."
            )
        
        return self


class DetallePartidaOut(BaseModel):
    id: UUID
    cuenta_id: UUID
    cuenta_codigo: str
    cuenta_nombre: str
    tipo_movimiento: str
    monto: Decimal


class PartidaOut(BaseModel):
    id: UUID
    numero_poliza: str | None = None
    fecha: date
    descripcion: str
    empresa_nombre: str | None = ""
    created_at: datetime
    is_active: bool = True
    fue_revertida: bool = False 
    tipo_origen: str = 'manual'
    detalles: List[DetallePartidaOut]

class LineaLibroDiario(BaseModel):
    partida_id: UUID
    numero_poliza: str | None = None
    fecha: date
    descripcion: str
    cuenta_id: UUID
    cuenta_codigo: str
    cuenta_nombre: str
    tipo_movimiento: str
    monto: Decimal

class ReversionPayload(BaseModel):
    fecha_reversion: date | None = None