# app/schemas/sat_libros.py
from datetime import date, datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class SatLibroLineaBase(BaseModel):
    factura_id: int  # ✅ BIGINT
    numero_secuencia: int
    fecha_documento: date
    numero_documento: str = Field(..., max_length=50)
    nit: str | None = Field(None, max_length=20)
    razon_social: str | None = Field(None, max_length=255)
    es_exento: bool = False
    es_exonerado: bool = False
    base_imponible: Decimal = Decimal("0.00")
    monto_exento: Decimal = Decimal("0.00")
    monto_iva: Decimal = Decimal("0.00")
    monto_total: Decimal = Decimal("0.00")
    credito_fiscal: Decimal = Decimal("0.00")
    debito_fiscal: Decimal = Decimal("0.00")


class SatLibroLineaResponse(SatLibroLineaBase):
    id: int  # ✅ BIGINT
    libro_id: int  # ✅ BIGINT
    model_config = ConfigDict(from_attributes=True)


class SatLibroBase(BaseModel):
    empresa_id: int  # ✅ BIGINT
    tipo_libro_id: int  # ✅ BIGINT
    regimen_fiscal_id: int  # ✅ BIGINT
    estado_id: int  # ✅ BIGINT
    anio_periodo: int = Field(..., ge=2020, le=2100)
    mes_periodo: int = Field(..., ge=1, le=12)


class SatLibroCreate(SatLibroBase):
    pass


class SatLibroResponse(SatLibroBase):
    id: int  # ✅ BIGINT
    total_lineas: int
    total_exento: Decimal
    total_base_imponible: Decimal
    total_iva: Decimal
    total_monto: Decimal
    finalizado_por: int | None = None  # ✅ BIGINT (ID del usuario)
    finalizado_el: datetime | None = None
    creado_el: datetime
    model_config = ConfigDict(from_attributes=True)


class SatLibroDetailResponse(SatLibroResponse):
    lineas: List[SatLibroLineaResponse] = []