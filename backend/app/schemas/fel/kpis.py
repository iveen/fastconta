"""
Schemas para KPIs de Facturas Electrónicas (FEL).
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class KPIsFinancieros(BaseModel):
    """KPIs financieros (montos en GTQ)."""
    compras_sin_iva: Decimal = Field(default=Decimal("0"), description="Total compras sin IVA (GTQ)")
    ventas_locales_sin_iva: Decimal = Field(default=Decimal("0"), description="Total ventas locales sin IVA (GTQ)")
    exportaciones_sin_iva: Decimal = Field(default=Decimal("0"), description="Total exportaciones sin IVA (GTQ)")
    credito_fiscal: Decimal = Field(default=Decimal("0"), description="IVA de compras (Crédito Fiscal)")
    debito_fiscal: Decimal = Field(default=Decimal("0"), description="IVA de ventas (Débito Fiscal)")
    iva_por_pagar: Decimal = Field(default=Decimal("0"), description="Débito - Crédito (IVA a pagar)")
    total_compras: Decimal = Field(default=Decimal("0"), description="Total compras con IVA")
    total_ventas: Decimal = Field(default=Decimal("0"), description="Total ventas con IVA")

    model_config = ConfigDict(from_attributes=True)


class KPIsConteos(BaseModel):
    """Conteo de documentos."""
    emitidos: int = 0
    recibidos: int = 0
    anulados: int = 0
    total: int = 0

    model_config = ConfigDict(from_attributes=True)


class SerieTemporalPoint(BaseModel):
    """Punto de serie temporal para gráficos."""
    periodo: str = Field(..., description="Período en formato YYYY-MM")
    compras: Decimal = Decimal("0")
    ventas_locales: Decimal = Decimal("0")
    exportaciones: Decimal = Decimal("0")
    credito_fiscal: Decimal = Decimal("0")
    debito_fiscal: Decimal = Decimal("0")
    documentos_emitidos: int = 0
    documentos_recibidos: int = 0

    model_config = ConfigDict(from_attributes=True)


class KPIsResponse(BaseModel):
    """Respuesta completa de KPIs FEL."""
    empresa_id: int
    empresa_nombre: Optional[str] = None
    fecha_inicio: date
    fecha_fin: date
    financieros: KPIsFinancieros
    conteos: KPIsConteos
    series_temporales: List[SerieTemporalPoint] = Field(
        default_factory=list,
        description="Datos agrupados por mes para gráficos"
    )

    model_config = ConfigDict(from_attributes=True)