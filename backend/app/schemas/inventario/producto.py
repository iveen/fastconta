from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProductoBase(BaseModel):
    codigo: str | None = Field(None, max_length=50)
    descripcion: str = Field(..., max_length=255)
    unidad_medida: str = Field("UND", max_length=20)
    cuenta_inventario_public_id: UUID | None = None


class ProductoCreate(ProductoBase):
    pass


class ProductoUpdate(BaseModel):
    codigo: str | None = Field(None, max_length=50)
    descripcion: str | None = Field(None, max_length=255)
    unidad_medida: str | None = Field(None, max_length=20)
    cuenta_inventario_public_id: UUID | None = None


class ProductoResponse(BaseModel):
    public_id: UUID
    empresa_id: UUID
    codigo: str | None
    descripcion: str
    unidad_medida: str
    cuenta_inventario_public_id: UUID | None = None
    is_active: bool
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)