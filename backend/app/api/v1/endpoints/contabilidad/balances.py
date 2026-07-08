# app/api/v1/endpoints/balances.py
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import case, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.export import (
    Column,
    ColumnAlignment,
    ColumnType,
    ExcelExporter,
    PdfExporter,
    ReportBuilder,
    ReportDefinition,
    Row,
)
from app.core.security import DataScope, get_data_scope
from app.db.session import get_public_db
from app.dependencies.empresa import get_active_empresa
from app.models.tenant_models import CuentaContable, DetallePartida, Empresa, Partida
from app.schemas.contabilidad.balances import (
    BalanceComprobacionResponse,
    BalanceGeneralResponse,
    EstadoResultadosResponse,
    FilaBalance,
)


class ReportFormat(str, Enum):
    JSON = "json"
    EXCEL = "excel"
    PDF = "pdf"


router = APIRouter()


# ============================================================
# Helper: Configurar search_path
# ============================================================
async def _set_schema_for_query(
    db: AsyncSession,
    scope: DataScope,
    tenant_id: int | None = None,
) -> str:
    if scope.role_code == "superadmin":
        if not tenant_id:
            raise HTTPException(400, detail="Superadmin debe especificar un tenant_id")
        res = await db.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"),
            {"tid": tenant_id},
        )
    else:
        res = await db.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"),
            {"tid": scope.tenant_id},
        )
    row = res.first()
    if not row:
        raise HTTPException(404, detail="Tenant no encontrado")
    schema_name = row[0]
    if not schema_name.replace("_", "").isalnum():
        raise HTTPException(500, detail="Schema con formato inválido")
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    return schema_name


# ============================================================
# Helper: Obtener empresa y validar
# ============================================================
async def _get_empresa(
    db: AsyncSession,
    empresa_id: int | None,
    empresa_from_header: Empresa | None,
) -> Empresa:
    empresa_id_final = empresa_id or (empresa_from_header.id if empresa_from_header else None)
    if not empresa_id_final:
        raise HTTPException(400, detail="Debe especificar un empresa_id o tener una empresa activa en el header")
    result = await db.execute(select(Empresa).where(Empresa.id == empresa_id_final))
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(400, detail="Empresa no encontrada")
    return empresa


# ============================================================
# Helper: Calcular saldos de cuentas
# ============================================================
async def _calcular_saldos(
    db: AsyncSession,
    cuentas: List[CuentaContable],
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
) -> List[FilaBalance]:
    filas = []
    for cuenta in cuentas:
        stmt = (
            select(
                func.coalesce(func.sum(
                    case((DetallePartida.tipo_movimiento == 'debe', DetallePartida.monto), else_=0)
                ), 0).label('sum_debe'),
                func.coalesce(func.sum(
                    case((DetallePartida.tipo_movimiento == 'haber', DetallePartida.monto), else_=0)
                ), 0).label('sum_haber'),
            )
            .select_from(DetallePartida)
            .join(Partida, DetallePartida.partida_id == Partida.id)
            .where(DetallePartida.cuenta_id == cuenta.id)
        )
        if fecha_inicio:
            stmt = stmt.where(Partida.fecha >= fecha_inicio)
        if fecha_fin:
            stmt = stmt.where(Partida.fecha <= fecha_fin)

        result_sum = await db.execute(stmt)
        sum_debe, sum_haber = result_sum.one()

        if cuenta.naturaleza == 'deudora':
            saldo = sum_debe - sum_haber
        else:
            saldo = sum_haber - sum_debe

        filas.append(FilaBalance(
            cuenta_id=cuenta.id,
            codigo=cuenta.codigo,
            nombre=cuenta.nombre,
            tipo=cuenta.tipo,
            naturaleza=cuenta.naturaleza,
            sum_debe=sum_debe,
            sum_haber=sum_haber,
            saldo=saldo,
        ))
    return filas


# ============================================================
# Helper: Construir reporte genérico
# ============================================================
def _build_report(
    title: str,
    subtitle: str,
    company_name: str,
    period: str,
    sections_data: List[dict],
) -> "ReportDefinition":
    columns = [
        Column("Código", "codigo", width=15, alignment=ColumnAlignment.LEFT),
        Column("Cuenta", "nombre", width=45, alignment=ColumnAlignment.LEFT),
        Column("Debe", "sum_debe", width=18, alignment=ColumnAlignment.RIGHT, type=ColumnType.CURRENCY),
        Column("Haber", "sum_haber", width=18, alignment=ColumnAlignment.RIGHT, type=ColumnType.CURRENCY),
        Column("Saldo", "saldo", width=18, alignment=ColumnAlignment.RIGHT, type=ColumnType.CURRENCY),
    ]

    builder = ReportBuilder() \
        .title(title) \
        .subtitle(subtitle) \
        .company(company_name) \
        .period(period) \
        .columns(columns)

    for section in sections_data:
        rows = [Row(data=fila.model_dump()) for fila in section["filas"]]
        totals = section.get("totals")
        builder.add_section(section["title"], rows, totals=totals)

    return builder.build()


# ============================================================
# Helper: Exportar según formato
# ============================================================
def _export_report(report, formato: ReportFormat, filename: str):
    if formato == ReportFormat.EXCEL:
        buffer = ExcelExporter.export(report)
        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"},
        )
    elif formato == ReportFormat.PDF:
        buffer = PdfExporter.export(report)
        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}.pdf"},
        )
    return None


# ============================================================
# 1. Balance de Comprobación
# ============================================================
@router.get("/comprobacion")
async def balance_comprobacion(
    empresa_id: int | None = Query(None, description="ID de la empresa"),
    fecha_inicio: date | None = Query(None, description="Fecha inicial"),
    fecha_fin: date | None = Query(None, description="Fecha final"),
    formato: ReportFormat = Query(ReportFormat.JSON, description="Formato de salida"),
    tenant_id: int | None = Query(None, description="ID del tenant (superadmin)"),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
    empresa_from_header: Empresa | None = Depends(get_active_empresa),
):
    await _set_schema_for_query(db, scope, tenant_id)
    empresa = await _get_empresa(db, empresa_id, empresa_from_header)

    result = await db.execute(
        select(CuentaContable)
        .where(CuentaContable.is_active.is_(True), CuentaContable.empresa_id == empresa.id)
        .order_by(CuentaContable.codigo)
    )
    cuentas = result.scalars().all()
    filas = await _calcular_saldos(db, cuentas, fecha_inicio, fecha_fin)

    if formato == ReportFormat.JSON:
        return BalanceComprobacionResponse(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            filas=filas,
        )

    period = f"{fecha_inicio} a {fecha_fin}" if fecha_inicio and fecha_fin else "Histórico"
    report = _build_report(
        title="Balance de Comprobación",
        subtitle=period,
        company_name=empresa.nombre,
        period=period,
        sections_data=[{"title": "", "filas": filas}],
    )
    return _export_report(report, formato, "balance_comprobacion")


# ============================================================
# 2. Estado de Resultados
# ============================================================
@router.get("/estado-resultados")
async def estado_resultados(
    empresa_id: int | None = Query(None),
    fecha_inicio: date = Query(..., description="Fecha de inicio"),
    fecha_fin: date = Query(..., description="Fecha de fin"),
    formato: ReportFormat = Query(ReportFormat.JSON),
    tenant_id: int | None = Query(None),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
    empresa_from_header: Empresa | None = Depends(get_active_empresa),
):
    await _set_schema_for_query(db, scope, tenant_id)
    empresa = await _get_empresa(db, empresa_id, empresa_from_header)

    result = await db.execute(
        select(CuentaContable)
        .where(
            CuentaContable.is_active.is_(True),
            CuentaContable.empresa_id == empresa.id,
            CuentaContable.tipo.in_(['ingreso', 'gasto']),
        )
        .order_by(CuentaContable.codigo)
    )
    cuentas = result.scalars().all()
    filas = await _calcular_saldos(db, cuentas, fecha_inicio, fecha_fin)

    ingresos = [f for f in filas if f.tipo == 'ingreso']
    gastos = [f for f in filas if f.tipo == 'gasto']
    total_ingresos = sum(f.saldo for f in ingresos if f.saldo > 0)
    total_gastos = sum(f.saldo for f in gastos if f.saldo > 0)
    utilidad_neta = total_ingresos - total_gastos

    if formato == ReportFormat.JSON:
        return EstadoResultadosResponse(
            empresa_id=empresa.id,
            empresa_nombre=empresa.nombre,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            ingresos=ingresos,
            total_ingresos=total_ingresos,
            gastos=gastos,
            total_gastos=total_gastos,
            utilidad_neta=utilidad_neta,
        )

    period = f"{fecha_inicio} a {fecha_fin}"
    report = _build_report(
        title="Estado de Resultados",
        subtitle=period,
        company_name=empresa.nombre,
        period=period,
        sections_data=[
            {
                "title": "INGRESOS",
                "filas": ingresos,
                "totals": {"codigo": "", "nombre": "Total Ingresos", "sum_debe": 0, "sum_haber": 0, "saldo": total_ingresos},
            },
            {
                "title": "GASTOS",
                "filas": gastos,
                "totals": {"codigo": "", "nombre": "Total Gastos", "sum_debe": 0, "sum_haber": 0, "saldo": total_gastos},
            },
            {
                "title": "UTILIDAD NETA",
                "filas": [],
                "totals": {"codigo": "", "nombre": "Utilidad Neta", "sum_debe": 0, "sum_haber": 0, "saldo": utilidad_neta},
            },
        ],
    )
    return _export_report(report, formato, "estado_resultados")


# ============================================================
# 3. Balance General
# ============================================================
@router.get("/balance-general")
async def balance_general(
    empresa_id: int | None = Query(None),
    fecha: date = Query(..., description="Fecha de corte"),
    formato: ReportFormat = Query(ReportFormat.JSON),
    tenant_id: int | None = Query(None),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
    empresa_from_header: Empresa | None = Depends(get_active_empresa),
):
    await _set_schema_for_query(db, scope, tenant_id)
    empresa = await _get_empresa(db, empresa_id, empresa_from_header)

    result = await db.execute(
        select(CuentaContable)
        .where(
            CuentaContable.is_active.is_(True),
            CuentaContable.empresa_id == empresa.id,
            CuentaContable.tipo.in_(['activo', 'pasivo', 'patrimonio']),
        )
        .order_by(CuentaContable.codigo)
    )
    cuentas = result.scalars().all()
    filas = await _calcular_saldos(db, cuentas, fecha_fin=fecha)

    activos = [f for f in filas if f.tipo == 'activo']
    pasivos = [f for f in filas if f.tipo == 'pasivo']
    patrimonio = [f for f in filas if f.tipo == 'patrimonio']
    total_activos = sum(f.saldo for f in activos)
    total_pasivos = sum(f.saldo for f in pasivos)
    total_patrimonio = sum(f.saldo for f in patrimonio)

    # Calcular utilidad del ejercicio
    stmt_ingresos = (
        select(func.coalesce(func.sum(DetallePartida.monto), 0))
        .select_from(DetallePartida)
        .join(Partida, DetallePartida.partida_id == Partida.id)
        .join(CuentaContable, DetallePartida.cuenta_id == CuentaContable.id)
        .where(
            CuentaContable.empresa_id == empresa.id,
            CuentaContable.tipo == 'ingreso',
            DetallePartida.tipo_movimiento == 'haber',
            Partida.fecha <= fecha,
        )
    )
    stmt_gastos = (
        select(func.coalesce(func.sum(DetallePartida.monto), 0))
        .select_from(DetallePartida)
        .join(Partida, DetallePartida.partida_id == Partida.id)
        .join(CuentaContable, DetallePartida.cuenta_id == CuentaContable.id)
        .where(
            CuentaContable.empresa_id == empresa.id,
            CuentaContable.tipo == 'gasto',
            DetallePartida.tipo_movimiento == 'debe',
            Partida.fecha <= fecha,
        )
    )
    total_ingresos = (await db.execute(stmt_ingresos)).scalar() or Decimal('0.00')
    total_gastos = (await db.execute(stmt_gastos)).scalar() or Decimal('0.00')
    utilidad_ejercicio = total_ingresos - total_gastos

    if formato == ReportFormat.JSON:
        return BalanceGeneralResponse(
            empresa_id=empresa.id,
            empresa_nombre=empresa.nombre,
            fecha=fecha,
            activos=activos,
            total_activos=total_activos,
            pasivos=pasivos,
            total_pasivos=total_pasivos,
            patrimonio=patrimonio,
            total_patrimonio=total_patrimonio,
            utilidad_ejercicio=utilidad_ejercicio,
        )

    period = f"Al {fecha.strftime('%d/%m/%Y')}"
    report = _build_report(
        title="Balance General",
        subtitle=period,
        company_name=empresa.nombre,
        period=period,
        sections_data=[
            {
                "title": "ACTIVOS",
                "filas": activos,
                "totals": {"codigo": "", "nombre": "Total Activos", "sum_debe": 0, "sum_haber": 0, "saldo": total_activos},
            },
            {
                "title": "PASIVOS",
                "filas": pasivos,
                "totals": {"codigo": "", "nombre": "Total Pasivos", "sum_debe": 0, "sum_haber": 0, "saldo": total_pasivos},
            },
            {
                "title": "PATRIMONIO",
                "filas": patrimonio,
                "totals": {"codigo": "", "nombre": "Total Patrimonio", "sum_debe": 0, "sum_haber": 0, "saldo": total_patrimonio},
            },
            {
                "title": "UTILIDAD DEL EJERCICIO",
                "filas": [],
                "totals": {"codigo": "", "nombre": "Utilidad del Ejercicio", "sum_debe": 0, "sum_haber": 0, "saldo": utilidad_ejercicio},
            },
        ],
    )
    return _export_report(report, formato, "balance_general")