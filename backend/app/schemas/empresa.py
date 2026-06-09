# app/schemas/empresa.py
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EmpresaCreate(BaseModel):
    nombre: str
    nit: str
    direccion: str | None = None


class EmpresaUpdate(BaseModel):
    """Schema para actualizar datos de empresa, incluyendo configuración contable"""
    nombre: str | None = None
    razon_social: str | None = None
    nombre_comercial: str | None = None
    nit: str | None = None
    direccion: str | None = None
    fecha_constitucion: date | None = None
    
    # 🔹 NUEVO: Configuración de cuentas para cierre contable
    cuenta_utilidad_periodo_id: UUID | None = None
    cuenta_utilidades_acumuladas_id: UUID | None = None


class EmpresaOut(BaseModel):
    id: UUID
    nombre: str
    razon_social: str | None = None
    nombre_comercial: str | None = None
    nit: str
    direccion: str | None
    fecha_constitucion: date | None = None
    created_at: datetime
    
    # 🔹 NUEVO: Devolver las cuentas configuradas (pueden ser None)
    cuenta_utilidad_periodo_id: UUID | None = None
    cuenta_utilidades_acumuladas_id: UUID | None = None

    model_config = ConfigDict(from_attributes=True)