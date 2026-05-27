# app/schemas/sat_libros.py
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
# Importamos los enums directamente de tus modelos para garantizar simetría absoluta
from app.models.tenant_models import TipoLibro, RegimenFiscal, EstadoLibro

class SatLibroLineaBase(BaseModel):
    factura_id: UUID
    numero_secuencia: int
    fecha_documento: date
    numero_documento: str = Field(..., max_length=50)
    nit: Optional[str] = Field(None, max_length=20)
    razon_social: Optional[str] = Field(None, max_length=255)
    es_exento: bool = False
    es_exonerado: bool = False
    base_imponible: Decimal = Decimal("0.00")
    monto_exento: Decimal = Decimal("0.00")
    monto_iva: Decimal = Decimal("0.00")
    monto_total: Decimal = Decimal("0.00")
    credito_fiscal: Decimal = Decimal("0.00")
    debito_fiscal: Decimal = Decimal("0.00")

class SatLibroLineaResponse(SatLibroLineaBase):
    id: UUID
    libro_id: UUID
    model_config = ConfigDict(from_attributes=True)

class SatLibroBase(BaseModel):
    empresa_id: UUID
    tipo_libro: TipoLibro
    regimen_fiscal: RegimenFiscal
    anio_periodo: int = Field(..., ge=2020, le=2100)
    mes_periodo: int = Field(..., ge=1, le=12)

class SatLibroCreate(SatLibroBase):
    pass

class SatLibroResponse(SatLibroBase):
    id: UUID
    estado: EstadoLibro
    total_lineas: int
    total_exento: Decimal
    total_base_imponible: Decimal
    total_iva: Decimal
    total_monto: Decimal
    finalizado_por: Optional[UUID] = None
    finalizado_el: Optional[datetime] = None
    creado_el: datetime
    model_config = ConfigDict(from_attributes=True)

class SatLibroDetailResponse(SatLibroResponse):
    lineas: List[SatLibroLineaResponse] = []