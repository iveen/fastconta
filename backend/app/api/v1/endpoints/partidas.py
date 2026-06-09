# app/api/v1/endpoints/partidas.py
from datetime import date
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import DataScope, get_data_scope
from app.crud.secuencias import get_next_poliza
from app.db.session import get_public_db, get_tenant_db
from app.models.tenant_models import (
    CuentaContable,
    DetallePartida,
    Empresa,
    Partida,
)
from app.schemas.partida import (
    DetallePartidaOut,
    LineaLibroDiario,
    PartidaCreate,
    PartidaOut,
)
from app.services.periodos import validar_periodo_abierto_por_fecha

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
# 1. Crear partida
# ==========================================
@router.post("/", response_model=PartidaOut, status_code=status.HTTP_201_CREATED)
async def crear_partida(
    payload: PartidaCreate,
    db: AsyncSession = Depends(get_tenant_db)
):
    try:
        # 1. Validar cuentas
        ids_cuentas = {d.cuenta_id for d in payload.detalles}
        result_cuentas = await db.execute(
            select(CuentaContable).options(selectinload(CuentaContable.empresa)).where(CuentaContable.id.in_(ids_cuentas))
        )
        cuentas = {c.id: c for c in result_cuentas.scalars().all()}
        
        if len(cuentas) != len(ids_cuentas):
            raise HTTPException(status_code=400, detail="Una o más cuentas no existen")
        
        for cuenta in cuentas.values():
            if not cuenta.activa:
                raise HTTPException(status_code=400, detail=f"La cuenta {cuenta.codigo} está inactiva")

        codigos_cuentas = [cuentas[d.cuenta_id].codigo for d in payload.detalles]
        if len(codigos_cuentas) != len(set(codigos_cuentas)):
            raise HTTPException(status_code=400, detail="No se permite usar la misma cuenta más de una vez en una partida")

        # Determinar empresa_id
        empresa_ids = {c.empresa_id for c in cuentas.values()}
        if len(empresa_ids) > 1:
            raise HTTPException(status_code=400, detail="Todas las cuentas deben pertenecer a la misma empresa")
        empresa_id = next(iter(empresa_ids))

        # ✅ 2. VALIDACIÓN DE PERÍODO CERRADO (Usando el servicio)
        await validar_periodo_abierto_por_fecha(db, empresa_id, payload.fecha)

        # 3. Generar número de póliza
        numero_poliza = payload.numero_poliza
        if not numero_poliza:
            schema_name = db.info["current_user"]["schema"]
            numero_poliza = await get_next_poliza(db, empresa_id, schema_name)
        else:
            existente = await db.execute(
                select(Partida).where(Partida.numero_poliza == numero_poliza, Partida.empresa_id == empresa_id)
            )
            if existente.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="El número de póliza ya existe para esta empresa")

        # 4. Crear partida y detalles (Operación Atómica)
        partida = Partida(
            fecha=payload.fecha,
            descripcion=payload.descripcion,
            numero_poliza=numero_poliza,
            empresa_id=empresa_id,
        )
        db.add(partida)
        await db.flush()

        for det in payload.detalles:
            db.add(DetallePartida(
                partida_id=partida.id,
                cuenta_id=det.cuenta_id,
                tipo_movimiento=det.tipo_movimiento,
                monto=det.monto
            ))

        await db.commit()
        
        # 5. Construir respuesta desde memoria
        empresa_nombre = cuentas[payload.detalles[0].cuenta_id].empresa.nombre if payload.detalles else ""
        
        return PartidaOut(
            id=partida.id,
            numero_poliza=partida.numero_poliza,
            fecha=partida.fecha,
            descripcion=partida.descripcion,
            empresa_nombre=empresa_nombre,
            created_at=partida.created_at,
            detalles=[
                DetallePartidaOut(
                    id=det.id, cuenta_id=det.cuenta_id,
                    cuenta_codigo=cuentas[det.cuenta_id].codigo,
                    cuenta_nombre=cuentas[det.cuenta_id].nombre,
                    tipo_movimiento=det.tipo_movimiento, monto=det.monto
                ) for det in payload.detalles
            ]
        )

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno al crear la partida: {str(e)}")


# ==========================================
# 2. Modificar Partida (PUT)
# ==========================================
@router.put("/{partida_id}", response_model=PartidaOut)
async def modificar_partida(
    partida_id: UUID,
    payload: PartidaCreate,
    db: AsyncSession = Depends(get_tenant_db)
):
    try:
        stmt = select(Partida).where(Partida.id == partida_id)
        partida = (await db.execute(stmt)).scalar_one_or_none()
        if not partida:
            raise HTTPException(status_code=404, detail="Partida no encontrada")

        # ✅ VALIDACIÓN: La NUEVA fecha no debe estar en un período cerrado
        await validar_periodo_abierto_por_fecha(db, partida.empresa_id, payload.fecha)

        # Validar cuentas (misma lógica que en POST)
        ids_cuentas = {d.cuenta_id for d in payload.detalles}
        result_cuentas = await db.execute(
            select(CuentaContable).options(selectinload(CuentaContable.empresa)).where(CuentaContable.id.in_(ids_cuentas))
        )
        cuentas = {c.id: c for c in result_cuentas.scalars().all()}
        
        if len(cuentas) != len(ids_cuentas):
            raise HTTPException(status_code=400, detail="Una o más cuentas no existen")

        # Operación Atómica de Actualización
        # await db.execute(delete(DetallePartida).where(DetallePartida.partida_id == partida_id))
        
        partida.fecha = payload.fecha
        partida.descripcion = payload.descripcion
        await db.flush()

        for det in payload.detalles:
            db.add(DetallePartida(
                partida_id=partida.id,
                cuenta_id=det.cuenta_id,
                tipo_movimiento=det.tipo_movimiento,
                monto=det.monto
            ))

        await db.commit()

        empresa_nombre = cuentas[payload.detalles[0].cuenta_id].empresa.nombre if payload.detalles else ""
        return PartidaOut(
            id=partida.id,
            numero_poliza=partida.numero_poliza,
            fecha=partida.fecha,
            descripcion=partida.descripcion,
            empresa_nombre=empresa_nombre,
            created_at=partida.created_at,
            detalles=[
                DetallePartidaOut(
                    id=det.id, cuenta_id=det.cuenta_id,
                    cuenta_codigo=cuentas[det.cuenta_id].codigo,
                    cuenta_nombre=cuentas[det.cuenta_id].nombre,
                    tipo_movimiento=det.tipo_movimiento, monto=det.monto
                ) for det in payload.detalles
            ]
        )

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno al modificar la partida: {str(e)}")


# ==========================================
# 3. Eliminar Partida (SOFT DELETE)
# ==========================================
@router.delete("/{partida_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_partida(
    partida_id: UUID,
    db: AsyncSession = Depends(get_tenant_db)
):
    try:
        # Cargamos la partida con sus detalles para desactivarlos en conjunto
        stmt = select(Partida).options(selectinload(Partida.detalles)).where(Partida.id == partida_id)
        partida = (await db.execute(stmt)).scalar_one_or_none()
        
        if not partida:
            raise HTTPException(status_code=404, detail="Partida no encontrada")

        # Si ya está inactiva, consideramos la operación exitosa (idempotencia)
        if not partida.is_active:
            return None

        # ✅ VALIDACIÓN: No se puede "eliminar" si el período está cerrado
        await validar_periodo_abierto_por_fecha(db, partida.empresa_id, partida.fecha)

        # ✅ SOFT DELETE: Cambiar estado a inactivo
        partida.is_active = False
        
        # Desactivar también los detalles para consistencia en consultas directas
        for detalle in partida.detalles:
            detalle.is_active = False

        await db.commit()
        return None

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno al eliminar la partida: {str(e)}")
    
# ==========================================
# 2. Listar partidas (con filtro para superadmin)
# ==========================================
@router.get("/", response_model=List[PartidaOut])
async def listar_partidas(
    empresa_id: UUID | None = Query(None, description="Filtrar partidas por empresa"),
    tenant_id: str | None = Query(None, description="ID del tenant (requerido para superadmin)"),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    await _set_schema_for_query(db, scope, tenant_id)
    
    if empresa_id:
        result_emp = await db.execute(select(Empresa).where(Empresa.id == empresa_id))
        if not result_emp.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Empresa no encontrada")
    
    stmt = (select(Partida)
            .options(selectinload(Partida.detalles)
                     .selectinload(DetallePartida.cuenta)
                     .selectinload(CuentaContable.empresa),
                     selectinload(Partida.empresa))
            .order_by(Partida.fecha.desc()))

    if empresa_id:
        stmt = stmt.where(Partida.empresa_id == empresa_id)

    result = await db.execute(stmt)
    partidas = result.scalars().all()

    resp = []
    for p in partidas:
        empresa_nombre = p.empresa.nombre if p.empresa else ""
        detalles_out = [
            DetallePartidaOut(
                id=d.id,
                cuenta_id=d.cuenta_id,
                cuenta_codigo=d.cuenta.codigo,
                cuenta_nombre=d.cuenta.nombre,
                tipo_movimiento=d.tipo_movimiento,
                monto=d.monto
            ) for d in p.detalles if getattr(d, 'is_active', True)
        ]
        resp.append(PartidaOut(
            id=p.id,
            numero_poliza=p.numero_poliza,
            fecha=p.fecha,
            descripcion=p.descripcion,
            empresa_nombre=empresa_nombre,
            created_at=p.created_at,
            detalles=detalles_out
        ))
    return resp

# ==========================================
# 3. Libro Diario
# ==========================================
@router.get("/libro-diario", response_model=List[LineaLibroDiario])
async def libro_diario(
    empresa_id: UUID = Query(..., description="ID de la empresa"),
    fecha_inicio: date = Query(..., description="Fecha inicial (inclusive)"),
    fecha_fin: date = Query(..., description="Fecha final (inclusive)"),
    tenant_id: str | None= Query(None),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    await _set_schema_for_query(db, scope, tenant_id)
    
    result_emp = await db.execute(select(Empresa).where(Empresa.id == empresa_id))
    if not result_emp.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Empresa no encontrada")
    
    stmt = (
        select(Partida, DetallePartida, CuentaContable)
        .join(DetallePartida, Partida.id == DetallePartida.partida_id)
        .join(CuentaContable, DetallePartida.cuenta_id == CuentaContable.id)
        .where(
            CuentaContable.empresa_id == empresa_id,
            Partida.fecha >= fecha_inicio,
            Partida.fecha <= fecha_fin
        )
        .order_by(Partida.fecha, Partida.numero_poliza, CuentaContable.codigo)
    )

    result = await db.execute(stmt)
    rows = result.all()

    lineas = []
    for partida, detalle, cuenta in rows:
        lineas.append(LineaLibroDiario(
            partida_id=partida.id,
            numero_poliza=partida.numero_poliza,
            fecha=partida.fecha,
            descripcion=partida.descripcion,
            cuenta_id=cuenta.id,
            cuenta_codigo=cuenta.codigo,
            cuenta_nombre=cuenta.nombre,
            tipo_movimiento=detalle.tipo_movimiento,
            monto=detalle.monto
        ))

    return lineas

# ==========================================
# 4. Obtener partida por ID
# ==========================================
@router.get("/{partida_id}", response_model=PartidaOut)
async def get_partida(
    partida_id: str,
    tenant_id: str | None = Query(None),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    await _set_schema_for_query(db, scope, tenant_id)
    
    stmt = (select(Partida)
            .where(Partida.id == partida_id)
            .options(selectinload(Partida.detalles).selectinload(DetallePartida.cuenta).selectinload(CuentaContable.empresa)))
    result = await db.execute(stmt)
    partida = result.scalar_one_or_none()
    if not partida:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    
    detalles_out = [
        DetallePartidaOut(
            id=d.id,
            cuenta_id=d.cuenta_id,
            cuenta_codigo=d.cuenta.codigo,
            cuenta_nombre=d.cuenta.nombre,
            tipo_movimiento=d.tipo_movimiento,
            monto=d.monto
        ) for d in partida.detalles
    ]

    empresa_nombre = ""
    if partida.detalles:
        cuenta = partida.detalles[0].cuenta
        if cuenta and cuenta.empresa:
            empresa_nombre = cuenta.empresa.nombre

    return PartidaOut(
        id=partida.id,
        numero_poliza=partida.numero_poliza,
        fecha=partida.fecha,
        descripcion=partida.descripcion,
        empresa_nombre=empresa_nombre,
        created_at=partida.created_at,
        detalles=detalles_out
    )