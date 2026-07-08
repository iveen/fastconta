# app/schemas/activos_fijos.py
from datetime import date, datetime
from decimal import Decimal
from typing import List, Literal

from pydantic import BaseModel, Field


class CategoriaActivoFijoResponse(BaseModel):
    id: int  # ✅ BIGINT
    nombre: str
    codigo_prefijo: str
    descripcion: str | None = None
    tasa_minima_anual: Decimal
    tasa_maxima_anual: Decimal
    vida_util_meses_default: int

    model_config = {"from_attributes": True}


class ActivoFijoCreate(BaseModel):
    empresa_id: int  # ✅ BIGINT
    categoria_id: int  # ✅ BIGINT
    codigo_interno: str = Field(..., max_length=50)
    descripcion: str = Field(..., max_length=255)
    fecha_adquisicion: date
    valor_costo: Decimal = Field(..., gt=0)
    valor_residual: Decimal = Field(default=0, ge=0)
    tasa_depreciacion_anual_aplicada: Decimal = Field(..., ge=0, le=100)
    vida_util_meses_aplicada: int = Field(..., gt=0)
    cuenta_gasto_id: int  # ✅ BIGINT
    cuenta_depreciacion_acumulada_id: int  # ✅ BIGINT
    estado: Literal["activo", "totalmente_depreciado", "dado_baja", "vendido"] = "activo"


class ActivoFijoUpdate(BaseModel):
    categoria_id: int | None = None  # ✅ BIGINT
    codigo_interno: str | None = Field(None, max_length=50)
    descripcion: str | None = Field(None, max_length=255)
    fecha_adquisicion: date | None = None
    valor_costo: Decimal | None = Field(None, gt=0)
    valor_residual: Decimal | None = Field(None, ge=0)
    tasa_depreciacion_anual_aplicada: Decimal | None = Field(None, ge=0, le=100)
    vida_util_meses_aplicada: int | None = Field(None, gt=0)
    cuenta_gasto_id: int | None = None  # ✅ BIGINT
    cuenta_depreciacion_acumulada_id: int | None = None  # ✅ BIGINT
    estado: Literal["activo", "totalmente_depreciado", "dado_baja", "vendido"] | None = None


class ActivoFijoResponse(BaseModel):
    id: int  # ✅ BIGINT
    empresa_id: int  # ✅ BIGINT
    categoria_id: int  # ✅ BIGINT
    codigo_interno: str
    descripcion: str
    fecha_adquisicion: date
    valor_costo: Decimal
    valor_residual: Decimal
    tasa_depreciacion_anual_aplicada: Decimal
    vida_util_meses_aplicada: int
    cuenta_gasto_id: int | None = None  # ✅ BIGINT
    cuenta_depreciacion_acumulada_id: int | None = None  # ✅ BIGINT
    estado: str
    created_at: datetime
    updated_at: datetime | None = None

    # Relaciones
    categoria: CategoriaActivoFijoResponse | None = None

    model_config = {"from_attributes": True}


class ProcesarDepreciacionMensualRequest(BaseModel):
    empresa_id: int  # ✅ BIGINT
    anio_periodo: int = Field(..., ge=2020, le=2100)
    mes_periodo: int = Field(..., ge=1, le=12)


class ProcesarDepreciacionMensualResponse(BaseModel):
    exito: bool
    mensaje: str
    activos_procesados: int
    monto_total_depreciacion: Decimal
    partida_id_generada: int | None = None  # ✅ BIGINT


class TablaDepreciacionProyectadaItem(BaseModel):
    anio_periodo: int
    mes_periodo: int
    monto_depreciacion_mes: Decimal
    depreciacion_acumulada_hasta_fecha: Decimal
    valor_en_libros: Decimal
    es_historico: bool
    nota: str | None = None


class TablaDepreciacionProyectadaResponse(BaseModel):
    activo_id: int  # ✅ BIGINT
    codigo_interno: str
    descripcion: str
    valor_costo: Decimal
    valor_residual: Decimal
    proyeccion: List[TablaDepreciacionProyectadaItem]