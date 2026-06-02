# app/api/v1/endpoints/plan_cuentas.py
from datetime import date
from decimal import Decimal
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import DataScope, get_data_scope
from app.db.session import get_public_db, get_tenant_db
from app.models.tenant_models import CuentaContable, DetallePartida, Empresa, Partida
from app.schemas.balances import (
    BalanceComprobacionResponse,
    FilaBalance,
    LibroMayorResponse,
    MovimientoCuenta,
)
from app.schemas.plan_cuentas import CuentaCreate, CuentaOut, CuentaUpdate

router = APIRouter()

# ==========================================
# Helper: Configurar search_path según rol
# ==========================================
async def _set_schema_for_query(db: AsyncSession, scope: DataScope, tenant_id: str | None = None):
    """Configura el search_path correcto según el rol del usuario."""
    schema_name = None
    
    if scope.role_code == "superadmin":
        if not tenant_id:
            raise HTTPException(400, detail="Superadmin debe especificar un tenant_id")
        res = await db.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"), 
            {"tid": tenant_id}
        )
        row = res.first()
        if not row:
            raise HTTPException(404, detail="Tenant no encontrado")
        schema_name = row[0]
    else:
        res = await db.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"), 
            {"tid": str(scope.tenant_id)}
        )
        row = res.first()
        if not row:
            raise HTTPException(404, detail="Tenant no encontrado")
        schema_name = row[0]

    if not schema_name.replace("_", "").isalnum():
        raise HTTPException(500, detail="Schema con formato inválido")

    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    return schema_name

# ==========================================
# 1. Listar cuentas (con filtro para superadmin)
# ==========================================
@router.get("/", response_model=List[CuentaOut])
async def list_cuentas(
    empresa_id: UUID = Query(None, description="Filtrar por empresa"),
    tenant_id: str | None = Query(None, description="ID del tenant (requerido para superadmin)"),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    await _set_schema_for_query(db, scope, tenant_id)
    
    stmt = select(CuentaContable).order_by(CuentaContable.codigo)
    if empresa_id:
        stmt = stmt.where(CuentaContable.empresa_id == empresa_id)
    
    result = await db.execute(stmt)
    return result.scalars().all()

# ==========================================
# 2. Obtener cuenta por ID
# ==========================================
@router.get("/{cuenta_id}", response_model=CuentaOut)
async def get_cuenta(
    cuenta_id: str,
    tenant_id: str | None = Query(None),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    await _set_schema_for_query(db, scope, tenant_id)
    
    result = await db.execute(select(CuentaContable).where(CuentaContable.id == cuenta_id))
    cuenta = result.scalar_one_or_none()
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    return cuenta

# ==========================================
# 3. Crear cuenta (usa get_tenant_db para usuarios normales)
# ==========================================
@router.post("/", response_model=CuentaOut, status_code=status.HTTP_201_CREATED)
async def create_cuenta(
    payload: CuentaCreate, 
    db: AsyncSession = Depends(get_tenant_db)
):
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

# ==========================================
# 4. Actualizar cuenta
# ==========================================
@router.put("/{cuenta_id}", response_model=CuentaOut)
async def update_cuenta(
    cuenta_id: str, 
    payload: CuentaUpdate, 
    db: AsyncSession = Depends(get_tenant_db)
):
    result = await db.execute(select(CuentaContable).where(CuentaContable.id == cuenta_id))
    cuenta = result.scalar_one_or_none()
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    
    update_data = payload.dict(exclude_unset=True)
    if "empresa_id" in update_data:
        new_emp_id = update_data["empresa_id"]
        if new_emp_id != cuenta.empresa_id:
            result_emp = await db.execute(select(Empresa).where(Empresa.id == new_emp_id))
            if not result_emp.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Nueva empresa no encontrada")

    for field, value in update_data.items():
        setattr(cuenta, field, value)
    
    await db.commit()
    await db.refresh(cuenta)
    return cuenta

# ==========================================
# 5. Eliminar cuenta
# ==========================================
@router.delete("/{cuenta_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cuenta(
    cuenta_id: str, 
    db: AsyncSession = Depends(get_tenant_db)
):
    result = await db.execute(select(CuentaContable).where(CuentaContable.id == cuenta_id))
    cuenta = result.scalar_one_or_none()
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    await db.delete(cuenta)
    await db.commit()
    return None

# ==========================================
# 6. Libro Mayor de cuenta
# ==========================================
@router.get("/{cuenta_id}/movimientos", response_model=LibroMayorResponse)
async def libro_mayor_cuenta(
    cuenta_id: str,
    fecha_inicio: date = Query(..., description="Fecha inicial del período"),
    fecha_fin: date = Query(..., description="Fecha final del período"),
    tenant_id: str | None = Query(None),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    await _set_schema_for_query(db, scope, tenant_id)
    
    result = await db.execute(select(CuentaContable).where(CuentaContable.id == cuenta_id))
    cuenta = result.scalar_one_or_none()
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    
    stmt = (select(DetallePartida, Partida)
            .join(Partida, DetallePartida.partida_id == Partida.id)
            .where(
                DetallePartida.cuenta_id == cuenta_id,
                Partida.fecha >= fecha_inicio,
                Partida.fecha <= fecha_fin
            )
            .order_by(Partida.fecha, Partida.created_at))

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
        else:
            if cuenta.naturaleza == "acreedora":
                saldo += monto
            else:
                saldo -= monto

        movimientos.append(MovimientoCuenta(
            fecha=part.fecha,
            partida_id=part.id,
            numero_poliza=part.numero_poliza,
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

# ==========================================
# 7. Balance de Comprobación
# ==========================================
@router.get("/comprobacion", response_model=BalanceComprobacionResponse)
async def balance_comprobacion(
    fecha_inicio: date | None = Query(None),
    fecha_fin: date | None = Query(None),
    tenant_id: str | None = Query(None),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    await _set_schema_for_query(db, scope, tenant_id)
    
    result = await db.execute(
        select(CuentaContable)
        .where(CuentaContable.activa.is_(True))
        .order_by(CuentaContable.codigo)
    )
    cuentas = result.scalars().all()
    
    filas = []
    for cuenta in cuentas:
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