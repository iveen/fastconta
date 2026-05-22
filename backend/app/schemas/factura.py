from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

class FacturaDetalleOut(BaseModel):
    id: UUID
    factura_id: UUID
    cantidad: Decimal
    descripcion: str
    precio_unitario: Decimal
    total_linea: Decimal
    iva_linea: Decimal
    model_config = ConfigDict(from_attributes=True)

class FacturaOut(BaseModel):
    id: UUID
    empresa_id: UUID
    numero_autorizacion: str
    autorizacion_uuid: Optional[str] = None
    serie: Optional[str] = None
    numero: str
    tipo_documento: Optional[str] = None
    moneda: Optional[str] = None
    fecha_emision: datetime
    emisor_nit: str
    emisor_nombre: str
    receptor_nit: str
    receptor_nombre: str
    total_gravado: Decimal
    total_iva: Decimal
    total_exento: Decimal
    total: Decimal
    created_at: datetime
    detalles: List[FacturaDetalleOut] = []
    es_exportacion: bool = False

    model_config = ConfigDict(from_attributes=True)
