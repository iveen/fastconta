from decimal import Decimal
from typing import Literal

from app.core.export.builder import ReportBuilder
from app.core.export.excel_exporter import ExcelExporter
from app.core.export.models import (
    Column,
    ColumnAlignment,
    ColumnType,
    ReportDefinition,
    Row,
)
from app.core.export.pdf_exporter import PdfExporter
from app.models.tenant_models import InventarioItem, InventarioToma
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload


class ExportService:
    """Servicio para exportar inventarios usando la arquitectura genérica de reportes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def exportar_toma(
        self,
        toma_id: int,
        tenant_id: int,
        formato: Literal["excel", "pdf"] = "excel",
    ) -> tuple[bytes, str]:
        """
        Exporta una toma de inventario a Excel o PDF.

        Returns:
            tuple: (bytes del archivo, nombre del archivo)
        """
        # Cargar toma con relaciones (async eager loading)
        stmt = (
            select(InventarioToma)
            .options(
                selectinload(InventarioToma.items)
                    .joinedload(InventarioItem.bodega),
                selectinload(InventarioToma.items)
                    .joinedload(InventarioItem.producto)
                    .joinedload(InventarioItem.producto.cuenta_inventario),
                joinedload(InventarioToma.empresa),
            )
            .where(
                and_(
                    InventarioToma.id == toma_id,
                    InventarioToma.tenant_id == tenant_id,
                )
            )
        )
        result = await self.db.execute(stmt)
        toma = result.unique().scalar_one_or_none()

        if not toma:
            raise ValueError("Toma no encontrada")

        # Construir nombre del archivo
        nombre_base = (
            f"Inventario_{toma.empresa_id}_"
            f"{toma.anio_periodo}_{str(toma.mes_periodo).zfill(2)}_"
            f"{toma.fecha_corte.strftime('%Y%m%d')}"
        )
        extension = "xlsx" if formato == "excel" else "pdf"
        nombre_archivo = f"{nombre_base}.{extension}"

        # Construir reporte usando ReportBuilder
        report = self._construir_reporte(toma)

        # Exportar según formato
        if formato == "excel":
            buffer = ExcelExporter.export(report)
        else:
            buffer = PdfExporter.export(report)

        return buffer.getvalue(), nombre_archivo

    def _construir_reporte(self, toma: InventarioToma) -> ReportDefinition:
        """Construye el ReportDefinition para el inventario."""
        empresa_nombre = toma.empresa.nombre if toma.empresa else f"Empresa {toma.empresa_id}"
        periodo_texto = f"{toma.anio_periodo}/{str(toma.mes_periodo).zfill(2)}"

        # === DEFINIR COLUMNAS ===
        columnas_detalle = [
            Column(header="Código", key="codigo", width=15,
                   alignment=ColumnAlignment.LEFT, type=ColumnType.TEXT),
            Column(header="Descripción", key="descripcion", width=40,
                   alignment=ColumnAlignment.LEFT, type=ColumnType.TEXT),
            Column(header="Bodega", key="bodega", width=15,
                   alignment=ColumnAlignment.LEFT, type=ColumnType.TEXT),
            Column(header="UM", key="unidad", width=8,
                   alignment=ColumnAlignment.CENTER, type=ColumnType.TEXT),
            Column(header="Cantidad", key="cantidad", width=12,
                   alignment=ColumnAlignment.RIGHT, type=ColumnType.NUMBER),
            Column(header="Costo Unit.", key="costo_unitario", width=15,
                   alignment=ColumnAlignment.RIGHT, type=ColumnType.CURRENCY),
            Column(header="Costo Total", key="costo_total", width=15,
                   alignment=ColumnAlignment.RIGHT, type=ColumnType.CURRENCY),
        ]

        # === CONSTRUIR REPORTE ===
        builder = ReportBuilder()
        builder.title("INVENTARIO FÍSICO")
        builder.subtitle(f"Fecha de Corte: {toma.fecha_corte.strftime('%d/%m/%Y')}")
        builder.company(empresa_nombre)
        builder.period(f"Período Fiscal: {periodo_texto}")
        builder.generated_by("FastConta")
        builder.orientation("landscape")
        builder.columns(columnas_detalle)

        # === SECCIÓN 1: DETALLE COMPLETO ===
        rows_detalle = []
        bodega_actual = None

        items_ordenados = sorted(
            toma.items,
            key=lambda x: (
                x.bodega_codigo or (x.bodega.nombre if x.bodega else "Sin Bodega"),
                x.codigo or "",
            ),
        )

        for item in items_ordenados:
            bodega_nombre = (
                item.bodega_codigo or (item.bodega.nombre if item.bodega else "Sin Bodega")
            )

            if bodega_actual and bodega_actual != bodega_nombre:
                rows_detalle.append(Row(
                    data={
                        "codigo": "", "descripcion": "", "bodega": "",
                        "unidad": "", "cantidad": "",
                        "costo_unitario": "", "costo_total": "",
                    },
                    bold=True,
                    background_color="#E0E0E0",
                ))

            bodega_actual = bodega_nombre

            rows_detalle.append(Row(
                data={
                    "codigo": item.codigo or "",
                    "descripcion": item.descripcion,
                    "bodega": bodega_nombre,
                    "unidad": item.unidad_medida or "UND",
                    "cantidad": item.cantidad,
                    "costo_unitario": item.costo_unitario,
                    "costo_total": item.costo_total,
                },
            ))

        totales_detalle = {
            "codigo": "", "descripcion": "", "bodega": "",
            "unidad": "", "cantidad": "", "costo_unitario": "",
            "costo_total": toma.valor_total,
        }

        builder.add_section(
            title="DETALLE DEL INVENTARIO",
            rows=rows_detalle,
            totals=totales_detalle,
            bold_title=True,
        )

        # === SECCIÓN 2: RESUMEN POR BODEGA ===
        resumen_bodegas: dict[str, dict] = {}
        for item in toma.items:
            bodega_nombre = (
                item.bodega_codigo or (item.bodega.nombre if item.bodega else "Sin Bodega")
            )
            if bodega_nombre not in resumen_bodegas:
                resumen_bodegas[bodega_nombre] = {
                    "total_items": 0,
                    "valor_total": Decimal("0.00"),
                }
            resumen_bodegas[bodega_nombre]["total_items"] += 1
            resumen_bodegas[bodega_nombre]["valor_total"] += item.costo_total

        rows_resumen = [
            Row(data={
                "bodega": bodega,
                "total_items": data["total_items"],
                "valor_total": data["valor_total"],
            })
            for bodega, data in sorted(
                resumen_bodegas.items(),
                key=lambda x: x[1]["valor_total"],
                reverse=True,
            )
        ]

        totales_resumen = {
            "bodega": "TOTAL GENERAL",
            "total_items": toma.total_items,
            "valor_total": toma.valor_total,
        }

        builder.add_section(
            title="RESUMEN POR BODEGA",
            rows=rows_resumen,
            totals=totales_resumen,
            bold_title=True,
        )

        # === SECCIÓN 3: RESUMEN POR CUENTA CONTABLE (si aplica) ===
        resumen_cuentas: dict[str, dict] = {}
        for item in toma.items:
            if item.producto and item.producto.cuenta_inventario:
                cuenta = item.producto.cuenta_inventario
                key = f"{cuenta.codigo} - {cuenta.nombre}"
                if key not in resumen_cuentas:
                    resumen_cuentas[key] = {
                        "codigo": cuenta.codigo,
                        "nombre": cuenta.nombre,
                        "total_items": 0,
                        "valor_total": Decimal("0.00"),
                    }
                resumen_cuentas[key]["total_items"] += 1
                resumen_cuentas[key]["valor_total"] += item.costo_total

        if resumen_cuentas:
            columnas_cuentas = [
                Column(header="Código", key="codigo", width=15,
                       alignment=ColumnAlignment.LEFT, type=ColumnType.TEXT),
                Column(header="Cuenta", key="nombre", width=40,
                       alignment=ColumnAlignment.LEFT, type=ColumnType.TEXT),
                Column(header="Total Items", key="total_items", width=15,
                       alignment=ColumnAlignment.RIGHT, type=ColumnType.NUMBER),
                Column(header="Valor Total", key="valor_total", width=20,
                       alignment=ColumnAlignment.RIGHT, type=ColumnType.CURRENCY),
            ]

            rows_cuentas = [
                Row(data={
                    "codigo": data["codigo"],
                    "nombre": data["nombre"],
                    "total_items": data["total_items"],
                    "valor_total": data["valor_total"],
                })
                for key, data in sorted(
                    resumen_cuentas.items(),
                    key=lambda x: x[1]["codigo"],
                )
            ]

            totales_cuentas = {
                "codigo": "",
                "nombre": "TOTAL GENERAL",
                "total_items": toma.total_items,
                "valor_total": toma.valor_total,
            }

            builder.add_section(
                title="RESUMEN POR CUENTA CONTABLE",
                rows=rows_cuentas,
                totals=totales_cuentas,
                bold_title=True,
            )

        # === METADATA ADICIONAL ===
        metadata_text = (
            f"Tipo: {toma.tipo} | "
            f"Método: {toma.metodo_valuacion} | "
            f"Estado: {toma.estado}"
        )
        if toma.observaciones:
            metadata_text += f" | Observaciones: {toma.observaciones}"

        # Concatenar metadata al subtitle existente
        builder.subtitle(f"{builder._subtitle} | {metadata_text}")

        return builder.build()