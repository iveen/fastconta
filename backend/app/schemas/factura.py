

from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FacturaDetalleOut(BaseModel):
    id: UUID
    factura_id: UUID
    cantidad: Decimal
    descripcion: str
    precio_unitario: Decimal
    total_linea: Decimal
    iva_linea: Decimal
    bien_o_servicio: str = 'B'

    # Montos en GTQ
    precio_unitario_gtq: Decimal | None = None
    total_linea_gtq: Decimal | None = None
    iva_linea_gtq: Decimal | None = None
    
    model_config = ConfigDict(from_attributes=True)

class FacturaImpuestoEspecialOut(BaseModel):
    id: UUID
    tipo_codigo: str          # Coincide con 'petroleo', 'turismo_hospedaje', etc.
    monto: Decimal
    model_config = ConfigDict(from_attributes=True)

class FacturaOut(BaseModel):
    id: UUID
    empresa_id: UUID
    numero_autorizacion: str
    autorizacion_uuid: str | None = None
    serie: str | None = None
    numero: str
    fecha_emision: datetime
    
    # Normalizados
    tipo_documento: str | None = None
    moneda: str | None = None
    tipo_documento_desc: str | None = None  
    moneda_nombre: str | None = None
    
    emisor_nit: str
    emisor_nombre: str
    receptor_nit: str
    receptor_nombre: str
    total_gravado: Decimal
    total_iva: Decimal
    total_exento: Decimal
    total: Decimal
    tipo_cambio: Decimal | None = None
    es_exportacion: bool = False
    tipo_operacion: str | None = "Venta"
    estado: str | None  = 'Activa'
    
    # ✅ NUEVOS CAMPOS (Auditoría y Validación)
    xml_filename: str | None = None
    validado: bool = False
    fecha_validacion: datetime | None = None
    
    created_at: datetime
    detalles: List[FacturaDetalleOut] = []
    impuestos_especiales: List[FacturaImpuestoEspecialOut] = []
    
    model_config = ConfigDict(from_attributes=True)