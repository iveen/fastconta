"""
Servicio de KPIs para Facturas Electrónicas (FEL).
Consultas SQL optimizadas para PostgreSQL.
"""
import logging
from datetime import date
from decimal import Decimal
from typing import List

from app.schemas.fel.kpis import (
    KPIsConteos,
    KPIsFinancieros,
    KPIsResponse,
    SerieTemporalPoint,
)
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class FELKPIsService:
    """Servicio para calcular KPIs de facturas electrónicas."""

    @staticmethod
    async def get_kpis(
        db: AsyncSession,
        empresa_id: int,
        fecha_inicio: date,
        fecha_fin: date,
        empresa_nombre: str | None = None,
    ) -> KPIsResponse:
        """
        Calcula todos los KPIs para un rango de fechas.
        
        Args:
            db: Sesión de BD (con search_path ya configurado al schema del tenant)
            empresa_id: ID de la empresa
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
            empresa_nombre: Nombre de la empresa (opcional)
        """
        # 1. KPIs financieros agregados
        financieros = await FELKPIsService._calcular_financieros(
            db, empresa_id, fecha_inicio, fecha_fin
        )
        
        # 2. Conteos de documentos
        conteos = await FELKPIsService._calcular_conteos(
            db, empresa_id, fecha_inicio, fecha_fin
        )
        
        # 3. Series temporales (agrupadas por mes)
        series = await FELKPIsService._calcular_series_temporales(
            db, empresa_id, fecha_inicio, fecha_fin
        )
        
        return KPIsResponse(
            empresa_id=empresa_id,
            empresa_nombre=empresa_nombre,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            financieros=financieros,
            conteos=conteos,
            series_temporales=series,
        )

    @staticmethod
    async def _calcular_financieros(
        db: AsyncSession,
        empresa_id: int,
        fecha_inicio: date,
        fecha_fin: date,
    ) -> KPIsFinancieros:
        """
        Calcula KPIs financieros usando COALESCE para evitar NULLs.
        Usa los campos _gtq que ya tienen la conversión de moneda aplicada.
        """
        query = text("""
            SELECT
                -- Compras (sin IVA)
                COALESCE(SUM(
                    CASE WHEN tipo_operacion = 'Compra' 
                         AND estado != 'Anulada'
                         AND es_exportacion = false
                    THEN total_gravado_gtq ELSE 0 END
                ), 0) AS compras_sin_iva,
                
                -- Ventas locales (sin IVA)
                COALESCE(SUM(
                    CASE WHEN tipo_operacion = 'Venta' 
                         AND estado != 'Anulada'
                         AND es_exportacion = false
                    THEN total_gravado_gtq ELSE 0 END
                ), 0) AS ventas_locales_sin_iva,
                
                -- Exportaciones (sin IVA)
                COALESCE(SUM(
                    CASE WHEN tipo_operacion = 'Venta' 
                         AND estado != 'Anulada'
                         AND es_exportacion = true
                    THEN total_gravado_gtq ELSE 0 END
                ), 0) AS exportaciones_sin_iva,
                
                -- Crédito Fiscal (IVA de compras)
                COALESCE(SUM(
                    CASE WHEN tipo_operacion = 'Compra' 
                         AND estado != 'Anulada'
                    THEN total_iva_gtq ELSE 0 END
                ), 0) AS credito_fiscal,
                
                -- Débito Fiscal (IVA de ventas, excluye exportaciones que son exentas)
                COALESCE(SUM(
                    CASE WHEN tipo_operacion = 'Venta' 
                         AND estado != 'Anulada'
                         AND es_exportacion = false
                    THEN total_iva_gtq ELSE 0 END
                ), 0) AS debito_fiscal,
                
                -- Total compras (con IVA)
                COALESCE(SUM(
                    CASE WHEN tipo_operacion = 'Compra' AND estado != 'Anulada'
                    THEN total_gtq ELSE 0 END
                ), 0) AS total_compras,
                
                -- Total ventas (con IVA)
                COALESCE(SUM(
                    CASE WHEN tipo_operacion = 'Venta' AND estado != 'Anulada'
                    THEN total_gtq ELSE 0 END
                ), 0) AS total_ventas
                
            FROM facturas_electronicas
            WHERE empresa_id = :empresa_id
              AND fecha_emision BETWEEN :fecha_inicio AND :fecha_fin
        """)
        
        result = await db.execute(query, {
            "empresa_id": empresa_id,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
        })
        row = result.first()
        
        if not row:
            return KPIsFinancieros()
        
        credito = Decimal(str(row.credito_fiscal or 0))
        debito = Decimal(str(row.debito_fiscal or 0))
        
        return KPIsFinancieros(
            compras_sin_iva=Decimal(str(row.compras_sin_iva or 0)),
            ventas_locales_sin_iva=Decimal(str(row.ventas_locales_sin_iva or 0)),
            exportaciones_sin_iva=Decimal(str(row.exportaciones_sin_iva or 0)),
            credito_fiscal=credito,
            debito_fiscal=debito,
            iva_por_pagar=debito - credito,
            total_compras=Decimal(str(row.total_compras or 0)),
            total_ventas=Decimal(str(row.total_ventas or 0)),
        )

    @staticmethod
    async def _calcular_conteos(
        db: AsyncSession,
        empresa_id: int,
        fecha_inicio: date,
        fecha_fin: date,
    ) -> KPIsConteos:
        """Cuenta documentos emitidos, recibidos y anulados."""
        query = text("""
            SELECT
                COUNT(*) FILTER (WHERE tipo_operacion = 'Venta' AND estado != 'Anulada') AS emitidos,
                COUNT(*) FILTER (WHERE tipo_operacion = 'Compra' AND estado != 'Anulada') AS recibidos,
                COUNT(*) FILTER (WHERE estado = 'Anulada') AS anulados,
                COUNT(*) AS total
            FROM facturas_electronicas
            WHERE empresa_id = :empresa_id
              AND fecha_emision BETWEEN :fecha_inicio AND :fecha_fin
        """)
        
        result = await db.execute(query, {
            "empresa_id": empresa_id,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
        })
        row = result.first()
        
        if not row:
            return KPIsConteos()
        
        return KPIsConteos(
            emitidos=row.emitidos or 0,
            recibidos=row.recibidos or 0,
            anulados=row.anulados or 0,
            total=row.total or 0,
        )

    @staticmethod
    async def _calcular_series_temporales(
        db: AsyncSession,
        empresa_id: int,
        fecha_inicio: date,
        fecha_fin: date,
    ) -> List[SerieTemporalPoint]:
        """Agrupa datos por mes para gráficos de series temporales."""
        query = text("""
            SELECT
                TO_CHAR(fecha_emision, 'YYYY-MM') AS periodo,
                
                -- Compras (sin IVA)
                COALESCE(SUM(
                    CASE WHEN tipo_operacion = 'Compra' 
                         AND estado != 'Anulada'
                         AND es_exportacion = false
                    THEN total_gravado_gtq ELSE 0 END
                ), 0) AS compras,
                
                -- Ventas locales (sin IVA)
                COALESCE(SUM(
                    CASE WHEN tipo_operacion = 'Venta' 
                         AND estado != 'Anulada'
                         AND es_exportacion = false
                    THEN total_gravado_gtq ELSE 0 END
                ), 0) AS ventas_locales,
                
                -- Exportaciones
                COALESCE(SUM(
                    CASE WHEN tipo_operacion = 'Venta' 
                         AND estado != 'Anulada'
                         AND es_exportacion = true
                    THEN total_gravado_gtq ELSE 0 END
                ), 0) AS exportaciones,
                
                -- Crédito Fiscal
                COALESCE(SUM(
                    CASE WHEN tipo_operacion = 'Compra' 
                         AND estado != 'Anulada'
                    THEN total_iva_gtq ELSE 0 END
                ), 0) AS credito_fiscal,
                
                -- Débito Fiscal
                COALESCE(SUM(
                    CASE WHEN tipo_operacion = 'Venta' 
                         AND estado != 'Anulada'
                         AND es_exportacion = false
                    THEN total_iva_gtq ELSE 0 END
                ), 0) AS debito_fiscal,
                
                -- Documentos emitidos (no anulados)
                COUNT(*) FILTER (WHERE tipo_operacion = 'Venta' AND estado != 'Anulada') AS documentos_emitidos,
                
                -- Documentos recibidos (no anulados)
                COUNT(*) FILTER (WHERE tipo_operacion = 'Compra' AND estado != 'Anulada') AS documentos_recibidos
                
            FROM facturas_electronicas
            WHERE empresa_id = :empresa_id
              AND fecha_emision BETWEEN :fecha_inicio AND :fecha_fin
            GROUP BY TO_CHAR(fecha_emision, 'YYYY-MM')
            ORDER BY periodo ASC
        """)
        
        result = await db.execute(query, {
            "empresa_id": empresa_id,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
        })
        
        return [
            SerieTemporalPoint(
                periodo=row.periodo,
                compras=Decimal(str(row.compras or 0)),
                ventas_locales=Decimal(str(row.ventas_locales or 0)),
                exportaciones=Decimal(str(row.exportaciones or 0)),
                credito_fiscal=Decimal(str(row.credito_fiscal or 0)),
                debito_fiscal=Decimal(str(row.debito_fiscal or 0)),
                documentos_emitidos=row.documentos_emitidos or 0,
                documentos_recibidos=row.documentos_recibidos or 0,
            )
            for row in result
        ]