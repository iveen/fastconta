from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ItemBase(BaseModel):
    codigo: str | None = Field(None, max_length=50)
    descripcion: str = Field(..., max_length=255)
    unidad_medida: str | None = Field("UND", max_length=20)
    cantidad: Decimal = Field(..., ge=0)
    costo_unitario: Decimal = Field(..., gt=0)
    bodega_codigo: str | None = Field(None, max_length=20)
    producto_public_id: UUID | None = None
    bodega_public_id: UUID | None = None

    @field_validator("descripcion")
    @classmethod
    def descripcion_no_vacia(cls, v):
        if not v or not v.strip():
            raise ValueError("Descripción requerida")
        return v.strip()


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    cantidad: Decimal | None = Field(None, ge=0)
    costo_unitario: Decimal | None = Field(None, gt=0)
    descripcion: str | None = Field(None, max_length=255)
    bodega_codigo: str | None = Field(None, max_length=20)


class ItemResponse(ItemBase):
    public_id: UUID
    toma_public_id: UUID
    producto_public_id: UUID | None = None
    bodega_public_id: UUID | None = None
    costo_total: Decimal
    model_config = ConfigDict(from_attributes=True)