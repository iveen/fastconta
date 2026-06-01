

from datetime import date
from decimal import Decimal
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_tenant_db
from app.models.tenant_models import CuentaContable, DetallePartida, Empresa, Partida
from app.schemas.balances import (
    BalanceComprobacionResponse,
    EstadoResultadosResponse,
    FilaBalance,
)
from app.services.reportes_export import (
    generar_balance_comprobacion_excel,
    generar_balance_comprobacion_pdf,
    generar_balance_general_excel,
    generar_balance_general_pdf,
    generar_estado_resultados_excel,
    generar_estado_resultados_pdf,
)

router = APIRouter()

@router.get("/comprobacion", response_model=BalanceComprobacionResponse)
async def balance_comprobacion(
    empresa_id: UUID = Query(..., description="ID de la empresa para filtrar el balance"),
    fecha_inicio: date | None = Query(None, description="Fecha inicial (inclusive)"),
    fecha_fin: date | None = Query(None, description="Fecha final (inclusive)"),
    db: AsyncSession = Depends(get_tenant_db)
):
    # Validar que la empresa existe
    result_emp = await db.execute(select(Empresa).where(Empresa.id == empresa_id))
    if not result_emp.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Empresa no encontrada")

    # Obtener solo las cuentas activas de esa empresa
    result = await db.execute(
        select(CuentaContable)
        .where(CuentaContable.activa == True, CuentaContable.empresa_id == empresa_id)
        .order_by(CuentaContable.codigo)
    )
    cuentas = result.scalars().all()

    filas = []
    for cuenta in cuentas:
        # Calcular sumas de débito y crédito para esta cuenta
        stmt = (select(
                    func.coalesce(func.sum(
                        case((DetallePartida.tipo_movimiento == 'debe', DetallePartida.monto), else_=0)
                    ), 0).label('sum_debe'),
                    func.coalesce(func.sum(
                        case((DetallePartida.tipo_movimiento == 'haber', DetallePartida.monto), else_=0)
                    ), 0).label('sum_haber'))
                .select_from(DetallePartida)
                .join(Partida, DetallePartida.partida_id == Partida.id)
                .where(DetallePartida.cuenta_id == cuenta.id))
        if fecha_inicio:
            stmt = stmt.where(Partida.fecha >= fecha_inicio)
        if fecha_fin:
            stmt = stmt.where(Partida.fecha <= fecha_fin)

        result_sum = await db.execute(stmt)
        sum_debe, sum_haber = result_sum.one()

        # Calcular saldo según naturaleza
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
            saldo=saldo
        ))

    return BalanceComprobacionResponse(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        filas=filas
    )

@router.get("/estado-resultados", response_model=EstadoResultadosResponse)
async def estado_resultados(
    empresa_id: UUID = Query(..., description="ID de la empresa"),
    fecha_inicio: date = Query(..., description="Fecha de inicio del período"),
    fecha_fin: date = Query(..., description="Fecha de fin del período"),
    db: AsyncSession = Depends(get_tenant_db)
):
    # Validar que la empresa existe
    result_emp = await db.execute(select(Empresa).where(Empresa.id == empresa_id))
    empresa = result_emp.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=400, detail="Empresa no encontrada")

    # Obtener cuentas de tipo ingreso y gasto de la empresa
    result = await db.execute(
        select(CuentaContable)
        .where(
            CuentaContable.activa == True,
            CuentaContable.empresa_id == empresa_id,
            CuentaContable.tipo.in_(['ingreso', 'gasto'])
        )
        .order_by(CuentaContable.codigo)
    )
    cuentas = result.scalars().all()

    ingresos = []
    gastos = []
    total_ingresos = Decimal('0.00')
    total_gastos = Decimal('0.00')

    for cuenta in cuentas:
        # Calcular sumas de débito y crédito para esta cuenta en el período
        stmt = (select(
                    func.coalesce(func.sum(
                        case((DetallePartida.tipo_movimiento == 'debe', DetallePartida.monto), else_=0)
                    ), 0).label('sum_debe'),
                    func.coalesce(func.sum(
                        case((DetallePartida.tipo_movimiento == 'haber', DetallePartida.monto), else_=0)
                    ), 0).label('sum_haber'))
                .select_from(DetallePartida)
                .join(Partida, DetallePartida.partida_id == Partida.id)
                .where(
                    DetallePartida.cuenta_id == cuenta.id,
                    Partida.fecha >= fecha_inicio,
                    Partida.fecha <= fecha_fin
                ))

        result_sum = await db.execute(stmt)
        sum_debe, sum_haber = result_sum.one()

        # Calcular saldo según naturaleza
        if cuenta.naturaleza == 'deudora':
            saldo = sum_debe - sum_haber
        else:  # acreedora
            saldo = sum_haber - sum_debe

        fila = FilaBalance(
            cuenta_id=cuenta.id,
            codigo=cuenta.codigo,
            nombre=cuenta.nombre,
            tipo=cuenta.tipo,
            naturaleza=cuenta.naturaleza,
            sum_debe=sum_debe,
            sum_haber=sum_haber,
            saldo=saldo
        )

        if cuenta.tipo == 'ingreso':
            ingresos.append(fila)
            # Los ingresos normalmente tienen saldo acreedor (positivo)
            total_ingresos += saldo if saldo > 0 else Decimal('0.00')
        else:  # gasto
            gastos.append(fila)
            # Los gastos normalmente tienen saldo deudor (positivo)
            total_gastos += saldo if saldo > 0 else Decimal('0.00')

    utilidad_neta = total_ingresos - total_gastos

    return EstadoResultadosResponse(
        empresa_id=empresa.id,
        empresa_nombre=empresa.nombre,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        ingresos=ingresos,
        total_ingresos=total_ingresos,
        gastos=gastos,
        total_gastos=total_gastos,
        utilidad_neta=utilidad_neta
    )

class BalanceGeneralResponse(BaseModel):
    empresa_id: UUID
    empresa_nombre: str
    fecha: date
    activos: List[FilaBalance]
    total_activos: Decimal
    pasivos: List[FilaBalance]
    total_pasivos: Decimal
    patrimonio: List[FilaBalance]
    total_patrimonio: Decimal
    utilidad_ejercicio: Decimal

@router.get("/balance-general", response_model=BalanceGeneralResponse)
async def balance_general(
    empresa_id: UUID = Query(..., description="ID de la empresa"),
    fecha: date = Query(..., description="Fecha de corte del balance"),
    db: AsyncSession = Depends(get_tenant_db)
):
    # Validar empresa
    result_emp = await db.execute(select(Empresa).where(Empresa.id == empresa_id))
    empresa = result_emp.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=400, detail="Empresa no encontrada")

    # Obtener todas las cuentas de balance (activo, pasivo, patrimonio)
    result = await db.execute(
        select(CuentaContable)
        .where(
            CuentaContable.activa == True,
            CuentaContable.empresa_id == empresa_id,
            CuentaContable.tipo.in_(['activo', 'pasivo', 'patrimonio'])
        )
        .order_by(CuentaContable.codigo)
    )
    cuentas = result.scalars().all()

    activos = []
    pasivos = []
    patrimonio = []
    total_activos = Decimal('0.00')
    total_pasivos = Decimal('0.00')
    total_patrimonio = Decimal('0.00')

    for cuenta in cuentas:
        # Calcular saldo hasta la fecha de corte
        stmt = (select(
                    func.coalesce(func.sum(
                        case((DetallePartida.tipo_movimiento == 'debe', DetallePartida.monto), else_=0)
                    ), 0).label('sum_debe'),
                    func.coalesce(func.sum(
                        case((DetallePartida.tipo_movimiento == 'haber', DetallePartida.monto), else_=0)
                    ), 0).label('sum_haber'))
                .select_from(DetallePartida)
                .join(Partida, DetallePartida.partida_id == Partida.id)
                .where(
                    DetallePartida.cuenta_id == cuenta.id,
                    Partida.fecha <= fecha
                ))

        result_sum = await db.execute(stmt)
        sum_debe, sum_haber = result_sum.one()

        if cuenta.naturaleza == 'deudora':
            saldo = sum_debe - sum_haber
        else:
            saldo = sum_haber - sum_debe

        fila = FilaBalance(
            cuenta_id=cuenta.id,
            codigo=cuenta.codigo,
            nombre=cuenta.nombre,
            tipo=cuenta.tipo,
            naturaleza=cuenta.naturaleza,
            sum_debe=sum_debe,
            sum_haber=sum_haber,
            saldo=saldo
        )

        if cuenta.tipo == 'activo':
            activos.append(fila)
            total_activos += saldo
        elif cuenta.tipo == 'pasivo':
            pasivos.append(fila)
            total_pasivos += saldo
        elif cuenta.tipo == 'patrimonio':
            patrimonio.append(fila)
            total_patrimonio += saldo

    # Calcular utilidad del ejercicio (ingresos - gastos) desde inicio hasta la fecha
    stmt_ingresos = (select(func.coalesce(func.sum(DetallePartida.monto), 0))
                     .select_from(DetallePartida)
                     .join(Partida, DetallePartida.partida_id == Partida.id)
                     .join(CuentaContable, DetallePartida.cuenta_id == CuentaContable.id)
                     .where(
                         CuentaContable.empresa_id == empresa_id,
                         CuentaContable.tipo == 'ingreso',
                         DetallePartida.tipo_movimiento == 'haber',
                         Partida.fecha <= fecha
                     ))
    stmt_gastos = (select(func.coalesce(func.sum(DetallePartida.monto), 0))
                   .select_from(DetallePartida)
                   .join(Partida, DetallePartida.partida_id == Partida.id)
                   .join(CuentaContable, DetallePartida.cuenta_id == CuentaContable.id)
                   .where(
                       CuentaContable.empresa_id == empresa_id,
                       CuentaContable.tipo == 'gasto',
                       DetallePartida.tipo_movimiento == 'debe',
                       Partida.fecha <= fecha
                   ))

    result_ingresos = await db.execute(stmt_ingresos)
    total_ingresos = result_ingresos.scalar() or Decimal('0.00')

    result_gastos = await db.execute(stmt_gastos)
    total_gastos = result_gastos.scalar() or Decimal('0.00')

    utilidad_ejercicio = total_ingresos - total_gastos

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
        utilidad_ejercicio=utilidad_ejercicio
    )

# ---------- EXCEL ----------
@router.get("/comprobacion/excel")
async def balance_comprobacion_excel(
    empresa_id: UUID = Query(...),
    fecha_inicio: date = Query(...),
    fecha_fin: date = Query(...),
    db: AsyncSession = Depends(get_tenant_db)
):
    # Obtener los mismos datos que el endpoint JSON
    datos = await balance_comprobacion(empresa_id, fecha_inicio, fecha_fin, db)
    excel = generar_balance_comprobacion_excel(datos.dict())
    return StreamingResponse(
        excel,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=balance_comprobacion.xlsx"}
    )

@router.get("/estado-resultados/excel")
async def estado_resultados_excel(
    empresa_id: UUID = Query(...),
    fecha_inicio: date = Query(...),
    fecha_fin: date = Query(...),
    db: AsyncSession = Depends(get_tenant_db)
):
    datos = await estado_resultados(empresa_id, fecha_inicio, fecha_fin, db)
    excel = generar_estado_resultados_excel(datos.dict())
    return StreamingResponse(
        excel,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=estado_resultados.xlsx"}
    )

@router.get("/balance-general/excel")
async def balance_general_excel(
    empresa_id: UUID = Query(...),
    fecha: date = Query(...),
    db: AsyncSession = Depends(get_tenant_db)
):
    datos = await balance_general(empresa_id, fecha, db)
    excel = generar_balance_general_excel(datos.dict())
    return StreamingResponse(
        excel,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=balance_general.xlsx"}
    )

# ---------- PDF ----------
@router.get("/comprobacion/pdf")
async def balance_comprobacion_pdf(
    empresa_id: UUID = Query(...),
    fecha_inicio: date = Query(...),
    fecha_fin: date = Query(...),
    db: AsyncSession = Depends(get_tenant_db)
):
    datos = await balance_comprobacion(empresa_id, fecha_inicio, fecha_fin, db)
    pdf = generar_balance_comprobacion_pdf(datos.dict())
    return StreamingResponse(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=balance_comprobacion.pdf"}
    )

@router.get("/estado-resultados/pdf")
async def estado_resultados_pdf(
    empresa_id: UUID = Query(...),
    fecha_inicio: date = Query(...),
    fecha_fin: date = Query(...),
    db: AsyncSession = Depends(get_tenant_db)
):
    datos = await estado_resultados(empresa_id, fecha_inicio, fecha_fin, db)
    pdf = generar_estado_resultados_pdf(datos.dict())
    return StreamingResponse(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=estado_resultados.pdf"}
    )

@router.get("/balance-general/pdf")
async def balance_general_pdf(
    empresa_id: UUID = Query(...),
    fecha: date = Query(...),
    db: AsyncSession = Depends(get_tenant_db)
):
    datos = await balance_general(empresa_id, fecha, db)
    pdf = generar_balance_general_pdf(datos.dict())
    return StreamingResponse(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=balance_general.pdf"}
    )