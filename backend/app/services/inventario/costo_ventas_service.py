from datetime import date
from decimal import Decimal

from app.models.tenant_models import (
    FacturaElectronica,
    InventarioItem,
    InventarioToma,
)
from sqlalchemy import Date, and_, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession


class CostoVentasService:
    """
    Calcula el Costo de Ventas usando la fórmula clásica:

        CV = Inventario Inicial + Compras del Período - Inventario Final

    - Inventario Inicial: valuación de la toma anterior CONFIRMADA/CONTABILIZADA
    - Compras: facturas con tipo_operacion='Compra' en el período
    - Inventario Final: valuación de la toma actual
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calcular(self, toma_id: int, tenant_id: int) -> dict:
        # === Obtener toma actual ===
        stmt_toma = select(InventarioToma).where(
            and_(
                InventarioToma.id == toma_id,
                InventarioToma.tenant_id == tenant_id,
            )
        )
        result = await self.db.execute(stmt_toma)
        toma_actual = result.scalar_one_or_none()

        if not toma_actual:
            raise ValueError("Toma no encontrada")

        # === Inventario Final ===
        stmt_final = select(
            func.coalesce(func.sum(InventarioItem.costo_total), 0)
        ).where(InventarioItem.toma_id == toma_id)
        inv_final = (await self.db.execute(stmt_final)).scalar() or Decimal("0")

        # === Inventario Inicial (toma anterior CONFIRMADA/CONTABILIZADA) ===
        stmt_anterior = select(InventarioToma).where(
            and_(
                InventarioToma.tenant_id == tenant_id,
                InventarioToma.empresa_id == toma_actual.empresa_id,
                (
                    (InventarioToma.anio_periodo < toma_actual.anio_periodo) |
                    (
                        (InventarioToma.anio_periodo == toma_actual.anio_periodo) &
                        (InventarioToma.mes_periodo < toma_actual.mes_periodo)
                    )
                ),
                InventarioToma.estado.in_(["CONFIRMADO", "CONTABILIZADO"]),
            )
        ).order_by(
            InventarioToma.anio_periodo.desc(),
            InventarioToma.mes_periodo.desc(),
        )
        result_anterior = await self.db.execute(stmt_anterior)
        toma_anterior = result_anterior.scalar_one_or_none()

        inv_inicial = Decimal("0")
        if toma_anterior:
            stmt_inv_inicial = select(
                func.coalesce(func.sum(InventarioItem.costo_total), 0)
            ).where(InventarioItem.toma_id == toma_anterior.id)
            inv_inicial = (await self.db.execute(stmt_inv_inicial)).scalar() or Decimal("0")

        # === Compras del período ===
        fecha_desde = (
            toma_anterior.fecha_corte if toma_anterior
            else date(toma_actual.anio_periodo, 1, 1)
        )

        stmt_compras = select(
            func.coalesce(func.sum(FacturaElectronica.total_gtq), 0)
        ).where(
            and_(
                FacturaElectronica.empresa_id == toma_actual.empresa_id,
                FacturaElectronica.tipo_operacion == "Compra",
                FacturaElectronica.estado == "Activa",
                cast(FacturaElectronica.fecha_emision, Date) > fecha_desde,
                cast(FacturaElectronica.fecha_emision, Date) <= toma_actual.fecha_corte,
            )
        )
        compras = (await self.db.execute(stmt_compras)).scalar() or Decimal("0")

        costo_ventas = inv_inicial + compras - inv_final

        return {
            "toma_id": toma_id,
            "empresa_id": toma_actual.empresa_id,
            "periodo_actual": (
                f"{toma_actual.anio_periodo}-"
                f"{str(toma_actual.mes_periodo).zfill(2)}"
            ),
            "periodo_desde": toma_anterior.fecha_corte if toma_anterior else None,
            "periodo_hasta": toma_actual.fecha_corte,
            "inventario_inicial": inv_inicial,
            "compras_periodo": compras,
            "inventario_final": inv_final,
            "costo_ventas": costo_ventas,
        }