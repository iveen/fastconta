from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import date, datetime
from typing import List, Optional, Literal
from decimal import Decimal


class DetallePartidaCreate(BaseModel):
    cuenta_id: UUID
    tipo_movimiento: Literal["debe", "haber"]
    monto: Decimal = Field(..., gt=0, decimal_places=2)


class PartidaCreate(BaseModel):
    fecha: date
    descripcion: str
    numero_poliza: Optional[str] = None
    detalles: List[DetallePartidaCreate]

    @field_validator('detalles')
    @classmethod
    def partida_doble_valid(cls, v):
        if not v:
            raise ValueError('La partida debe tener al menos un detalle')
        total_debe = sum(d.monto for d in v if d.tipo_movimiento == 'debe')
        total_haber = sum(d.monto for d in v if d.tipo_movimiento == 'haber')
        if total_debe != total_haber:
            raise ValueError(f'Partida no balanceada: débito={total_debe}, crédito={total_haber}')
        return v


class DetallePartidaOut(BaseModel):
    id: UUID
    cuenta_id: UUID
    cuenta_codigo: str
    cuenta_nombre: str
    tipo_movimiento: str
    monto: Decimal


class PartidaOut(BaseModel):
    id: UUID
    numero: int
    numero_poliza: Optional[str] = None
    fecha: date
    descripcion: str
    empresa_nombre: Optional[str] = ""
    created_at: datetime
    detalles: List[DetallePartidaOut]