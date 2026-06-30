# app/api/v1/endpoints/partidas.py
import logging
from datetime import date
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import DataScope, get_data_scope
from app.crud.secuencias import get_next_poliza
from app.db.session import get_public_db, get_tenant_db
from app.dependencies.empresa import get_active_empresa
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
    ReversionPayload,
)
from app.services.periodos import validar_periodo_abierto_por_fecha

router = APIRouter()

logger = logging.getLogger(__name__)

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
            tipo_origen='manual',
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
            is_active=partida.is_active,
            fue_revertida=False,
            tipo_origen='manual',
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
        
        if not partida.is_active:
            raise HTTPException(status_code=400, detail="No se puede modificar una partida eliminada")

        # ✅ VALIDACIÓN CRÍTICA: No permitir eliminar pólizas de sistema
        if partida.tipo_origen in ['cierre', 'reversion_cierre']:
            raise HTTPException(
                status_code=403, 
                detail=f"No se puede modificar una póliza de {partida.tipo_origen.replace('_', ' ')}. "
                       "Este tipo de pólizas son generadas automáticamente por el sistema."
            )

        # ✅ VALIDACIÓN: La NUEVA fecha no debe estar en un período cerrado
        await validar_periodo_abierto_por_fecha(db, partida.empresa_id, payload.fecha)

        # Validar cuentas
        ids_cuentas = {d.cuenta_id for d in payload.detalles}
        result_cuentas = await db.execute(
            select(CuentaContable).options(selectinload(CuentaContable.empresa)).where(CuentaContable.id.in_(ids_cuentas))
        )
        cuentas = {c.id: c for c in result_cuentas.scalars().all()}
        
        if len(cuentas) != len(ids_cuentas):
            raise HTTPException(status_code=400, detail="Una o más cuentas no existen")

        # 🚨 CORRECCIÓN CRÍTICA: Eliminar los detalles antiguos antes de insertar los nuevos
        await db.execute(delete(DetallePartida).where(DetallePartida.partida_id == partida_id))
        
        # Actualizar cabecera
        partida.fecha = payload.fecha
        partida.descripcion = payload.descripcion
        
        # Si el usuario cambió el número de póliza, validarlo (opcional, pero recomendado)
        if payload.numero_poliza and payload.numero_poliza != partida.numero_poliza:
            existente = await db.execute(
                select(Partida).where(Partida.numero_poliza == payload.numero_poliza, Partida.empresa_id == partida.empresa_id, Partida.id != partida_id)
            )
            if existente.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="El número de póliza ya existe para esta empresa")
            partida.numero_poliza = payload.numero_poliza

        await db.flush()

        # Insertar nuevos detalles
        for det in payload.detalles:
            db.add(DetallePartida(
                partida_id=partida.id,
                cuenta_id=det.cuenta_id,
                tipo_movimiento=det.tipo_movimiento,
                monto=det.monto
            ))

        await db.commit()
        await db.refresh(partida, ['detalles']) # Refrescar para obtener los nuevos detalles con sus IDs

        # Reconstruir respuesta (simplificado para el ejemplo)
        empresa_nombre = cuentas[payload.detalles[0].cuenta_id].empresa.nombre if payload.detalles else ""
        
        # ... (Retornar PartidaOut igual que en tu código original, asegurando que usa partida.detalles actualizados)
        return PartidaOut(
            id=partida.id,
            numero_poliza=partida.numero_poliza,
            fecha=partida.fecha,
            descripcion=partida.descripcion,
            empresa_nombre=empresa_nombre,
            created_at=partida.created_at,
            is_active=partida.is_active,
            fue_revertida=partida.fue_revertida,
            tipo_origen=partida.tipo_origen,
            detalles=[
                DetallePartidaOut(
                    id=det.id, cuenta_id=det.cuenta_id,
                    cuenta_codigo=cuentas[det.cuenta_id].codigo,
                    cuenta_nombre=cuentas[det.cuenta_id].nombre,
                    tipo_movimiento=det.tipo_movimiento, monto=det.monto
                ) for det in partida.detalles
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

        # ✅ VALIDACIÓN CRÍTICA: No permitir eliminar pólizas de sistema
        if partida.tipo_origen in ['cierre', 'reversion_cierre']:
            raise HTTPException(
                status_code=403, 
                detail=f"No se puede eliminar una póliza de {partida.tipo_origen.replace('_', ' ')}. "
                       "Este tipo de pólizas son generadas automáticamente por el sistema."
            )

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
# 4. Listar partidas (con filtro para superadmin)
# ==========================================
@router.get("/", response_model=List[PartidaOut])
async def listar_partidas(
    empresa_id: UUID | None = Query(None, description="Filtrar partidas por empresa"),
    tenant_id: str | None = Query(None, description="ID del tenant (requerido para superadmin)"),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
    empresa_from_header: Empresa | None = Depends(get_active_empresa)
):
    await _set_schema_for_query(db, scope, tenant_id)

    empresa_id_final = empresa_id or (empresa_from_header.id if empresa_from_header else None)
    
    if empresa_id_final:
        result_emp = await db.execute(select(Empresa).where(Empresa.id == empresa_id_final))
        if not result_emp.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Empresa no encontrada")
    
    stmt = (select(Partida)
            .options(selectinload(Partida.detalles)
                     .selectinload(DetallePartida.cuenta)
                     .selectinload(CuentaContable.empresa),
                     selectinload(Partida.empresa))
            .order_by(Partida.fecha.desc()))

    if empresa_id_final:
        stmt = stmt.where(Partida.empresa_id == empresa_id_final)

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
            fue_revertida=p.fue_revertida,
            tipo_origen=p.tipo_origen,
            is_active=p.is_active,
            detalles=detalles_out
        ))
    return resp


# ==========================================
# 5. Libro Diario
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
# 6. Revertir Partida (SQL PURO - SIN search_path)
# ==========================================
@router.post("/{partida_id}/revertir", response_model=PartidaOut, status_code=status.HTTP_201_CREATED)
async def revertir_partida(
    partida_id: UUID,
    payload: ReversionPayload,
    tenant_id: str | None = Query(None),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    try:
        # ✅ CONFIGURAR SEARCH_PATH Y OBTENER SCHEMA_NAME
        schema_name = await _set_schema_for_query(db, scope, tenant_id)
        
        # ✅ 1. Obtener partida original con SQL PURO (especificando schema explícitamente)
        stmt_original = text(f"""
            SELECT 
                p.id, p.numero_poliza, p.fecha, p.descripcion, p.empresa_id, p.is_active, p.fue_revertida,
                d.id as detalle_id, d.cuenta_id, d.tipo_movimiento, d.monto,
                c.codigo as cuenta_codigo, c.nombre as cuenta_nombre,
                e.nombre as empresa_nombre
            FROM {schema_name}.partidas p
            JOIN {schema_name}.detalle_partidas d ON p.id = d.partida_id
            JOIN {schema_name}.plan_cuentas c ON d.cuenta_id = c.id
            JOIN {schema_name}.empresas e ON c.empresa_id = e.id
            WHERE p.id = :partida_id
            ORDER BY d.id
        """)
        
        result = await db.execute(stmt_original, {"partida_id": partida_id})
        rows = result.all()
        
        if not rows:
            raise HTTPException(status_code=404, detail="Partida no encontrada")
        
        # Procesar primera fila
        primera_fila = rows[0]
        
        # Validaciones
        if not primera_fila.is_active:
            raise HTTPException(status_code=400, detail="No se puede revertir una partida eliminada")
        
        if primera_fila.fue_revertida:
            raise HTTPException(
                status_code=400, 
                detail="Esta partida ya fue revertida. Si necesitas restituir el efecto, debes revertir la partida de reversión generada."
            )
        
        # ✅ VALIDACIÓN CRÍTICA: No permitir revertir pólizas de sistema
        if primera_fila.tipo_origen in ['cierre', 'reversion_cierre']:
            raise HTTPException(
                status_code=403, 
                detail=f"No se puede revertir una póliza de {primera_fila.tipo_origen.replace('_', ' ')}. "
                       "Este tipo de pólizas son generadas automáticamente por el sistema y no pueden ser modificadas ni revertidas desde la interfaz."
            )

        # Reconstruir detalles desde las filas
        detalles_originales = []
        for row in rows:
            detalles_originales.append({
                "cuenta_id": row.cuenta_id,
                "cuenta_codigo": row.cuenta_codigo,
                "cuenta_nombre": row.cuenta_nombre,
                "tipo_movimiento": row.tipo_movimiento,
                "monto": float(row.monto)
            })

        # 2. Determinar fecha de reversión (hoy por defecto)
        fecha_rev = payload.fecha_reversion or date.today()

        # 3. Validar que el período de la reversión esté abierto
        await validar_periodo_abierto_por_fecha(db, primera_fila.empresa_id, fecha_rev)

        # 4. Generar nuevo número de póliza
        nuevo_numero_poliza = await get_next_poliza(db, primera_fila.empresa_id, schema_name)

        # 5. Crear la nueva partida de reversión con SQL
        desc_reversion = f"Reversión Póliza {primera_fila.numero_poliza} - {primera_fila.descripcion}"
        
        stmt_insert_partida = text(f"""
            INSERT INTO {schema_name}.partidas 
            (fecha, descripcion, numero_poliza, empresa_id, is_active, fue_revertida, partida_reversion_id)
            VALUES (:fecha, :descripcion, :numero_poliza, :empresa_id, true, false, NULL)
            RETURNING id, created_at
        """)
        
        result_partida = await db.execute(stmt_insert_partida, {
            "fecha": fecha_rev,
            "descripcion": desc_reversion,
            "numero_poliza": nuevo_numero_poliza,
            "empresa_id": primera_fila.empresa_id
        })
        
        partida_reversion_data = result_partida.first()
        partida_reversion_id = partida_reversion_data.id
        created_at = partida_reversion_data.created_at

        # 6. Invertir los detalles (Debe <-> Haber) con SQL
        for det_orig in detalles_originales:
            tipo_invertido = "haber" if det_orig["tipo_movimiento"] == "debe" else "debe"
            
            stmt_insert_detalle = text(f"""
                INSERT INTO {schema_name}.detalle_partidas 
                (partida_id, cuenta_id, tipo_movimiento, monto, is_active)
                VALUES (:partida_id, :cuenta_id, :tipo_movimiento, :monto, true)
            """)
            
            await db.execute(stmt_insert_detalle, {
                "partida_id": partida_reversion_id,
                "cuenta_id": det_orig["cuenta_id"],
                "tipo_movimiento": tipo_invertido,
                "monto": det_orig["monto"]
            })

        # 7. MARCAR PARTIDA ORIGINAL COMO REVERTIDA
        stmt_update_original = text(f"""
            UPDATE {schema_name}.partidas 
            SET fue_revertida = true, partida_reversion_id = :partida_reversion_id
            WHERE id = :partida_id
        """)
        
        await db.execute(stmt_update_original, {
            "partida_reversion_id": partida_reversion_id,
            "partida_id": partida_id
        })

        await db.commit()

        # 8. Construir respuesta
        detalles_out = [
            DetallePartidaOut(
                id=UUID(int=i),  # IDs temporales
                cuenta_id=det["cuenta_id"],
                cuenta_codigo=det["cuenta_codigo"],
                cuenta_nombre=det["cuenta_nombre"],
                tipo_movimiento="haber" if det["tipo_movimiento"] == "debe" else "debe",
                monto=det["monto"]
            ) for i, det in enumerate(detalles_originales, start=1)
        ]

        return PartidaOut(
            id=partida_reversion_id,
            numero_poliza=nuevo_numero_poliza,
            fecha=fecha_rev,
            descripcion=desc_reversion,
            empresa_nombre=primera_fila.empresa_nombre or "",
            created_at=created_at,
            is_active=True,
            fue_revertida=False,
            tipo_origen='reversion',
            detalles=detalles_out
        )

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno al revertir la partida: {str(e)}")

    
# ==========================================
# 7. Obtener partida por ID
# ==========================================
@router.get("/{partida_id}", response_model=PartidaOut)
async def get_partida(
    partida_id: UUID,
    tenant_id: str | None = Query(None),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    await _set_schema_for_query(db, scope, tenant_id)
    
    stmt = (select(Partida)
            .where(Partida.id == partida_id)
            .options(
                selectinload(Partida.detalles)
                .selectinload(DetallePartida.cuenta)
                .selectinload(CuentaContable.empresa),
                selectinload(Partida.empresa)
            ))
    
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

    empresa_nombre = partida.empresa.nombre if partida.empresa else ""

    return PartidaOut(
        id=partida.id,
        numero_poliza=partida.numero_poliza,
        fecha=partida.fecha,
        descripcion=partida.descripcion,
        empresa_nombre=empresa_nombre,
        created_at=partida.created_at,
        is_active=partida.is_active,
        fue_revertida=partida.fue_revertida,
        tipo_origen=partida.tipo_origen,
        detalles=detalles_out
    )