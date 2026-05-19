from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.session import get_tenant_db
from app.models.tenant_models import Partida, DetallePartida, CuentaContable, \
    Empresa, PeriodoFiscal
from app.schemas.partida import PartidaCreate, PartidaOut, DetallePartidaOut
from uuid import UUID
from typing import Optional
from app.crud.secuencias import get_next_poliza
from datetime import date

router = APIRouter()

@router.post("/", response_model=PartidaOut, status_code=status.HTTP_201_CREATED)
async def crear_partida(payload: PartidaCreate, db: AsyncSession = Depends(get_tenant_db)):
    # Validar cuentas
    ids_cuentas = {d.cuenta_id for d in payload.detalles}
    result_cuentas = await db.execute(select(CuentaContable).where(CuentaContable.id.in_(ids_cuentas)))
    cuentas = {c.id: c for c in result_cuentas.scalars().all()}
    if len(cuentas) != len(ids_cuentas):
        raise HTTPException(status_code=400, detail="Una o más cuentas no existen")
    
    # --- Validación de Cuentas Activas y No Duplicadas
    for cuenta in cuentas.values():
        if not cuenta.activa:
            raise HTTPException(status_code=400, detail=f"La cuenta {cuenta.codigo} está inactiva")
    
    # Verificar duplicados en los detalles
    codigos_cuentas = [cuentas[d.cuenta_id].codigo for d in payload.detalles]
    if len(codigos_cuentas) != len(set(codigos_cuentas)):
        raise HTTPException(status_code=400, detail="No se permite usar la misma cuenta más de una vez en una partida")

    # --- Validación de período fiscal ---
    fecha_partida = payload.fecha
    # Buscar un periodo que contenga la fecha
    result_periodo = await db.execute(
        select(PeriodoFiscal).where(
            PeriodoFiscal.fecha_inicio <= fecha_partida,
            PeriodoFiscal.fecha_fin >= fecha_partida
        )
    )
    periodo = result_periodo.scalar_one_or_none()
    if not periodo:
        raise HTTPException(status_code=400, detail="No existe un período fiscal definido para la fecha de la partida")
    if periodo.cerrado:
        raise HTTPException(status_code=400, detail=f"El período fiscal '{periodo.nombre}' está cerrado")

    # Validar que todas las cuentas son de la misma empresa
    empresa_ids = {c.empresa_id for c in cuentas.values()}
    if len(empresa_ids) > 1:
        raise HTTPException(status_code=400, detail="Todas las cuentas deben pertenecer a la misma empresa")
    empresa_id = next(iter(empresa_ids))

    # Generar numero_poliza automático si no se proporciona
    numero_poliza = payload.numero_poliza

    # Validar unicidad de numero_poliza si se proporciona
    if not numero_poliza:
        numero_poliza = await get_next_poliza(db, empresa_id)
    else:
        existente = await db.execute(select(Partida).where(Partida.numero_poliza == numero_poliza))
        if existente.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="El número de póliza ya existe")

    # Crear partida (sin empresa_id)
    partida = Partida(
        fecha=payload.fecha,
        descripcion=payload.descripcion,
        numero_poliza=numero_poliza,
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

    # Recuperar con detalles, cuentas y empresa
    stmt = (select(Partida)
            .where(Partida.id == partida.id)
            .options(selectinload(Partida.detalles).selectinload(DetallePartida.cuenta).selectinload(CuentaContable.empresa)))
    result = await db.execute(stmt)
    partida = result.scalar_one()

    # Obtener nombre de empresa desde la primera cuenta
    empresa_nombre = ""
    if partida.detalles:
        cuenta = partida.detalles[0].cuenta
        if cuenta and cuenta.empresa:
            empresa_nombre = cuenta.empresa.nombre

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
    return PartidaOut(
        id=partida.id,
        numero=partida.numero,
        numero_poliza=partida.numero_poliza,
        fecha=partida.fecha,
        descripcion=partida.descripcion,
        empresa_nombre=empresa_nombre,
        created_at=partida.created_at,
        detalles=detalles_out
    )

@router.get("/", response_model=list[PartidaOut])
async def listar_partidas(
    empresa_id: Optional[UUID] = Query(None, description="Filtrar partidas por empresa"),
    db: AsyncSession = Depends(get_tenant_db)
):
    # Validar que la empresa existe si se proporciona el ID
    if empresa_id:
        result_emp = await db.execute(select(Empresa).where(Empresa.id == empresa_id))
        if not result_emp.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Empresa no encontrada")

    # Construir consulta base
    stmt = (select(Partida)
            .options(selectinload(Partida.detalles)
                     .selectinload(DetallePartida.cuenta)
                     .selectinload(CuentaContable.empresa))
            .order_by(Partida.fecha.desc()))

    # Aplicar filtro por empresa si se solicita
    if empresa_id:
        subquery = (select(DetallePartida.partida_id)
                    .join(CuentaContable, DetallePartida.cuenta_id == CuentaContable.id)
                    .where(CuentaContable.empresa_id == empresa_id))
        stmt = stmt.where(Partida.id.in_(subquery))

    result = await db.execute(stmt)
    partidas = result.scalars().all()

    # Construir respuesta (igual que antes)
    resp = []
    for p in partidas:
        empresa_nombre = ""
        if p.detalles:
            cuenta = p.detalles[0].cuenta
            if cuenta and cuenta.empresa:
                empresa_nombre = cuenta.empresa.nombre

        detalles_out = [
            DetallePartidaOut(
                id=d.id,
                cuenta_id=d.cuenta_id,
                cuenta_codigo=d.cuenta.codigo,
                cuenta_nombre=d.cuenta.nombre,
                tipo_movimiento=d.tipo_movimiento,
                monto=d.monto
            ) for d in p.detalles
        ]
        resp.append(PartidaOut(
            id=p.id,
            numero=p.numero,
            numero_poliza=p.numero_poliza,
            fecha=p.fecha,
            descripcion=p.descripcion,
            empresa_nombre=empresa_nombre,
            created_at=p.created_at,
            detalles=detalles_out
        ))
    return resp