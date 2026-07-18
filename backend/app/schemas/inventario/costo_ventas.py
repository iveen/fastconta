from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class CostoVentasResponse(BaseModel):
    toma_public_id: str
    empresa_public_id: str
    periodo_actual: str
    periodo_desde: date | None = None
    periodo_hasta: date
    inventario_inicial: Decimal
    compras_periodo: Decimal
    inventario_final: Decimal
    costo_ventas: Decimal