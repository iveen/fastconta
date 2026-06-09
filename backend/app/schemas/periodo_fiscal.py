# app/schemas/periodo_fiscal.py

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PeriodoFiscalCreate(BaseModel):
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    empresa_id: UUID

class PeriodoFiscalOut(BaseModel):
    id: UUID
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    empresa_id: UUID  
    cerrado: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


