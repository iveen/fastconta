from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TomaBase(BaseModel):
    anio_periodo: int = Field(..., ge=2000, le=2100)
    mes_periodo: int = Field(..., ge=1, le=12)
    fecha_corte: date
    tipo: str = Field("FISCAL", pattern="^(FISCAL|INTERNO|AJUSTE)$")
    metodo_valuacion: str = Field(
        "COSTO_PROMEDIO",
        pattern="^(COSTO_PROMEDIO|PEPS|IDENTIFICACION_ESPECIFICA)$"
    )
    observaciones: str | None = None

    @model_validator(mode="after")
    def validar_coherencia_periodo(self):
        if (self.fecha_corte.year != self.anio_periodo or
                self.fecha_corte.month != self.mes_periodo):
            raise ValueError(
                f"La fecha de corte ({self.fecha_corte}) debe estar "
                f"dentro del período {self.anio_periodo}/{str(self.mes_periodo).zfill(2)}"
            )
        if self.tipo == "FISCAL":
            es_fiscal = (
                (self.fecha_corte.month == 6 and self.fecha_corte.day == 30) or
                (self.fecha_corte.month == 12 and self.fecha_corte.day == 31)
            )
            if not es_fiscal:
                raise ValueError(
                    "Inventario FISCAL debe ser al 30/jun o 31/dic"
                )
        return self


class TomaCreate(TomaBase):
    empresa_public_id: UUID


class TomaUpdate(BaseModel):
    fecha_corte: date | None = None
    tipo: str | None = Field(None, pattern="^(FISCAL|INTERNO|AJUSTE)$")
    metodo_valuacion: str | None = Field(
        None,
        pattern="^(COSTO_PROMEDIO|PEPS|IDENTIFICACION_ESPECIFICA)$"
    )
    estado: str | None = Field(
        None, pattern="^(BORRADOR|CONFIRMADO|CONTABILIZADO)$"
    )
    observaciones: str | None = None


class ItemResumen(BaseModel):
    public_id: UUID
    codigo: str | None
    descripcion: str
    cantidad: Decimal
    costo_unitario: Decimal
    costo_total: Decimal
    bodega_codigo: str | None
    unidad_medida: str | None
    model_config = ConfigDict(from_attributes=True)


class TomaResponse(TomaBase):
    public_id: UUID
    empresa_public_id: UUID
    estado: str
    partida_ajuste_public_id: UUID | None = None
    total_items: int = 0
    valor_total: Decimal = Decimal("0.00")
    created_at: datetime | None = None
    updated_at: datetime | None = None
    items: list[ItemResumen] = []
    model_config = ConfigDict(from_attributes=True)


class TomaListResponse(TomaBase):
    public_id: UUID
    empresa_public_id: UUID
    estado: str
    total_items: int = 0
    valor_total: Decimal = Decimal("0.00")
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)