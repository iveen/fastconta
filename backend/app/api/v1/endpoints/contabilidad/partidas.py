# app/api/v1/endpoints/partidas.py
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import DataScope, get_data_scope
from app.db.session import get_public_db, get_tenant_db
from app.dependencies.empresa import get_active_empresa
from app.models.tenant_models import Empresa
from app.schemas.contabilidad.partida import (
    DetallePartidaOut,
    LineaLibroDiario,
    PartidaCreate,
    PartidaOut,
    ReversionPayload,
)
from app.services.contabilidad.partida_service import PartidaService

router = APIRouter()


def get_service(db: AsyncSession = Depends(get_tenant_db)) -> PartidaService:
    return PartidaService(db)


# ============================================================
# Helper: Configurar search_path según rol
# ============================================================
async def _set_schema_for_query(
    db: AsyncSession, 
    scope: DataScope, 
    tenant_id: int | None = None  # ✅ int (era str)
) -> str:
    """Configura el search_path correcto según el rol del usuario y retorna el schema_name."""
    if scope.role_code == "superadmin":
        if not tenant_id:
            raise HTTPException(400, detail="Superadmin debe especificar un tenant_id")
        res = await db.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"),
            {"tid": tenant_id}  # ✅ int (no str)
        )
    else:
        res = await db.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"),
            {"tid": scope.tenant_id}  # ✅ int (no str)
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
# 1. Crear partida
# ============================================================
@router.post("/", response_model=PartidaOut, status_code=status.HTTP_201_CREATED)
async def crear_partida(
    payload: PartidaCreate,
    service: PartidaService = Depends(get_service)
):
    try:
        detalles = [d.model_dump() for d in payload.detalles]
        schema_name = service.db.info.get("current_user", {}).get("schema")
        
        return await service.crear_partida(
            fecha=payload.fecha,
            descripcion=payload.descripcion,
            detalles=detalles,
            numero_poliza=payload.numero_poliza,
            schema_name=schema_name
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ============================================================
# 2. Modificar partida
# ============================================================
@router.put("/{partida_id}", response_model=PartidaOut)
async def modificar_partida(
    partida_id: int,
    payload: PartidaCreate,
    service: PartidaService = Depends(get_service)
):
    try:
        detalles = [d.model_dump() for d in payload.detalles]
        return await service.modificar_partida(
            partida_id=partida_id,
            fecha=payload.fecha,
            descripcion=payload.descripcion,
            detalles=detalles,
            numero_poliza=payload.numero_poliza
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ============================================================
# 3. Eliminar partida
# ============================================================
@router.delete("/{partida_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_partida(
    partida_id: int,
    service: PartidaService = Depends(get_service)
):
    try:
        await service.eliminar_partida(partida_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ============================================================
# 4. Listar partidas
# ============================================================
@router.get("/", response_model=list[PartidaOut])
async def listar_partidas(
    empresa_id: int | None = Query(None),
    tenant_id: int | None = Query(None),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
    empresa_from_header: Empresa | None = Depends(get_active_empresa)
):
    # Configurar search_path (lógica existente)
    # ...
    
    service = PartidaService(db)
    partidas = await service.listar_partidas(empresa_id)
    
    return [
        PartidaOut(
            id=p.id,
            numero_poliza=p.numero_poliza,
            fecha=p.fecha,
            descripcion=p.descripcion,
            empresa_nombre=p.empresa.nombre if p.empresa else "",
            created_at=p.created_at,
            is_active=p.is_active,
            fue_revertida=p.fue_revertida,
            tipo_origen=p.tipo_origen,
            detalles=[
                DetallePartidaOut(
                    id=d.id,
                    cuenta_id=d.cuenta_id,
                    cuenta_codigo=d.cuenta.codigo,
                    cuenta_nombre=d.cuenta.nombre,
                    tipo_movimiento=d.tipo_movimiento,
                    monto=d.monto
                ) for d in p.detalles
            ]
        ) for p in partidas
    ]


# ============================================================
# 5. Libro diario
# ============================================================
@router.get("/libro-diario", response_model=list[LineaLibroDiario])
async def libro_diario(
    empresa_id: int,
    fecha_inicio: date,
    fecha_fin: date,
    service: PartidaService = Depends(get_service)
):
    try:
        lineas = await service.obtener_libro_diario(empresa_id, fecha_inicio, fecha_fin)
        return [LineaLibroDiario(**linea) for linea in lineas]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ============================================================
# 6. Revertir partida
# ============================================================
@router.post("/{partida_id}/revertir", response_model=PartidaOut, status_code=status.HTTP_201_CREATED)
async def revertir_partida(
    partida_id: int,  # ✅ BIGINT (era UUID)
    payload: ReversionPayload,
    tenant_id: int | None = Query(None),  # ✅ BIGINT (era str)
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    # 1. ✅ Configurar search_path y obtener schema_name (Esto faltaba)
    schema_name = await _set_schema_for_query(db, scope, tenant_id)
    
    # 2. Ejecutar lógica del servicio
    service = PartidaService(db)
    try:
        return await service.revertir_partida(
            partida_id=partida_id,
            fecha_reversion=payload.fecha_reversion,
            schema_name=schema_name
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")