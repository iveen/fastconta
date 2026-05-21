from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from typing import Optional
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy.orm import selectinload
from app.db.session import get_tenant_db
from app.models.tenant_models import CuentaContable, Partida, DetallePartida, Empresa
from app.schemas.plan_cuentas import CuentaCreate, CuentaUpdate, CuentaOut
from app.schemas.balances import LibroMayorResponse, MovimientoCuenta, BalanceComprobacionResponse, FilaBalance
from uuid import UUID

router = APIRouter()

@router.get("/", response_model=list[CuentaOut])
async def list_cuentas(
    empresa_id: UUID = Query(None, description="Filtrar por empresa"),
    db: AsyncSession = Depends(get_tenant_db)
):
    stmt = select(CuentaContable).order_by(CuentaContable.codigo)
    if empresa_id:
        stmt = stmt.where(CuentaContable.empresa_id == empresa_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{cuenta_id}", response_model=CuentaOut)
async def get_cuenta(cuenta_id: str, db: AsyncSession = Depends(get_tenant_db)):
    result = await db.execute(select(CuentaContable).where(CuentaContable.id == cuenta_id))
    cuenta = result.scalar_one_or_none()
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    return cuenta

@router.post("/", response_model=CuentaOut, status_code=status.HTTP_201_CREATED)
async def create_cuenta(payload: CuentaCreate, db: AsyncSession = Depends(get_tenant_db)):
    # Verificar unicidad de código
    empresa_res = await db.execute(select(Empresa).where(Empresa.id == payload.empresa_id))
    if not empresa_res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Empresa no encontrada")
    existe = await db.execute(select(CuentaContable).where(CuentaContable.codigo == payload.codigo))
    if existe.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="El código de cuenta ya existe")
    cuenta = CuentaContable(**payload.dict())
    db.add(cuenta)
    await db.commit()
    await db.refresh(cuenta)
    return cuenta

@router.put("/{cuenta_id}", response_model=CuentaOut)
async def update_cuenta(cuenta_id: str, payload: CuentaUpdate, db: AsyncSession = Depends(get_tenant_db)):
    result = await db.execute(select(CuentaContable).where(CuentaContable.id == cuenta_id))
    cuenta = result.scalar_one_or_none()
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    update_data = payload.dict(exclude_unset=True)

    # Si se cambia empresa_id, validar que la nueva empresa exista
    if "empresa_id" in update_data:
        new_emp_id = update_data["empresa_id"]
        if new_emp_id != cuenta.empresa_id:  # solo validar si cambió
            result_emp = await db.execute(select(Empresa).where(Empresa.id == new_emp_id))
            if not result_emp.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Nueva empresa no encontrada")

    for field, value in update_data.items():
        setattr(cuenta, field, value)
    await db.commit()
    await db.refresh(cuenta)
    return cuenta

@router.delete("/{cuenta_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cuenta(cuenta_id: str, db: AsyncSession = Depends(get_tenant_db)):
    result = await db.execute(select(CuentaContable).where(CuentaContable.id == cuenta_id))
    cuenta = result.scalar_one_or_none()
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    await db.delete(cuenta)
    await db.commit()
    return None

@router.get("/{cuenta_id}/movimientos", response_model=LibroMayorResponse)
async def libro_mayor_cuenta(
    cuenta_id: str,
    fecha_inicio: date = Query(..., description="Fecha inicial del período"),
    fecha_fin: date = Query(..., description="Fecha final del período"),
    db: AsyncSession = Depends(get_tenant_db)
):
    # Obtener la cuenta
    result = await db.execute(select(CuentaContable).where(CuentaContable.id == cuenta_id))
    cuenta = result.scalar_one_or_none()
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    # Construir query de movimientos
    stmt = (select(DetallePartida, Partida)
            .join(Partida, DetallePartida.partida_id == Partida.id)
            .where(DetallePartida.cuenta_id == cuenta_id))
    stmt = stmt.where(Partida.fecha >= fecha_inicio)
    stmt = stmt.where(Partida.fecha <= fecha_fin)
    stmt = stmt.order_by(Partida.fecha, Partida.created_at)

    result = await db.execute(stmt)
    rows = result.all()

    movimientos = []
    saldo = Decimal('0.00')
    for det, part in rows:
        monto = det.monto
        if det.tipo_movimiento == "debe":
            if cuenta.naturaleza == "deudora":
                saldo += monto
            else:
                saldo -= monto
        else:  # haber
            if cuenta.naturaleza == "acreedora":
                saldo += monto
            else:
                saldo -= monto

        movimientos.append(MovimientoCuenta(
            fecha=part.fecha,
            partida_id=part.id,
            descripcion_partida=part.descripcion,
            tipo_movimiento=det.tipo_movimiento,
            monto=monto
        ))

    return LibroMayorResponse(
        cuenta_id=cuenta.id,
        cuenta_codigo=cuenta.codigo,
        cuenta_nombre=cuenta.nombre,
        naturaleza=cuenta.naturaleza,
        movimientos=movimientos,
        saldo_actual=saldo
    )

@router.get("/comprobacion", response_model=BalanceComprobacionResponse)
async def balance_comprobacion(
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicial (inclusive)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha final (inclusive)"),
    db: AsyncSession = Depends(get_tenant_db)
):
    # Obtener todas las cuentas activas
    result = await db.execute(
        select(CuentaContable)
        .where(CuentaContable.activa == True)
        .order_by(CuentaContable.codigo)
    )
    cuentas = result.scalars().all()

    filas = []
    for cuenta in cuentas:
        # Construir subconsulta de sumas de débito y crédito
        stmt = (
            select(
                func.coalesce(func.sum(
                    case(
                        (DetallePartida.tipo_movimiento == 'debe', DetallePartida.monto),
                        else_=0
                    )
                ), 0).label('sum_debe'),
                func.coalesce(func.sum(
                    case(
                        (DetallePartida.tipo_movimiento == 'haber', DetallePartida.monto),
                        else_=0
                    )
                ), 0).label('sum_haber')
            )
            .select_from(DetallePartida)
            .join(Partida, DetallePartida.partida_id == Partida.id)
            .where(DetallePartida.cuenta_id == cuenta.id)
        )
        if fecha_inicio:
            stmt = stmt.where(Partida.fecha >= fecha_inicio)
        if fecha_fin:
            stmt = stmt.where(Partida.fecha <= fecha_fin)

        result = await db.execute(stmt)
        sum_debe, sum_haber = result.one()

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