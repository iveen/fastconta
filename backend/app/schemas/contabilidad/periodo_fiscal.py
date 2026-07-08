# app/schemas/periodo_fiscal.py
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class PeriodoFiscalCreate(BaseModel):
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    empresa_id: int  # ✅ BIGINT (era UUID)


class PeriodoFiscalOut(BaseModel):
    id: int  # ✅ BIGINT (era UUID)
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    empresa_id: int  # ✅ BIGINT (era UUID)
    cerrado: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)