from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from typing import Optional
from datetime import date
from decimal import Decimal

from app.db.session import get_tenant_db
from app.models.tenant_models import CuentaContable, DetallePartida, Partida, Empresa
from app.schemas.balances import BalanceComprobacionResponse, FilaBalance
from uuid import UUID

router = APIRouter()

@router.get("/comprobacion", response_model=BalanceComprobacionResponse)
async def balance_comprobacion(
    empresa_id: UUID = Query(..., description="ID de la empresa para filtrar el balance"),
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicial (inclusive)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha final (inclusive)"),
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