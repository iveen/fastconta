# app/api/v1/endpoints/activos_fijos.py
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import Integer, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.empresa_utils import verificar_acceso_empresa
from app.core.security import DataScope, get_data_scope
from app.core.tenant_utils import set_tenant_search_path
from app.db.session import get_public_db, get_tenant_db
from app.dependencies.empresa import get_active_empresa  # ✅ NUEVO
from app.models.global_models import CategoriaActivoFijo
from app.models.tenant_models import ActivoFijo, Empresa  # ✅ Agregado Empresa
from app.schemas.activos_fijos import (
    ActivoFijoCreate,
    ActivoFijoResponse,
    ActivoFijoUpdate,
    CategoriaActivoFijoResponse,
    ProcesarDepreciacionMensualRequest,
    ProcesarDepreciacionMensualResponse,
    TablaDepreciacionProyectadaResponse,
)
from app.services import activos_fijos_service

# ==============================================================================
# ROUTER
# ==============================================================================
router = APIRouter(prefix="/activos-fijos", tags=["Activos Fijos"])

# ==============================================================================
# RUTAS ESTÁTICAS (DEBEN IR PRIMERO)
# ==============================================================================
@router.get("/categorias", response_model=List[CategoriaActivoFijoResponse])
async def listar_categorias_activos(
    db: AsyncSession = Depends(get_public_db)
):
    """Catálogo global de categorías (schema public)."""
    stmt = select(CategoriaActivoFijo).where(CategoriaActivoFijo.is_active.is_(True))
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/siguiente-codigo")
async def obtener_siguiente_codigo(
    empresa_id: uuid.UUID | None = Query(None, description="ID de la empresa (opcional, usa X-Company-Id)"),
    categoria_id: uuid.UUID = Query(..., description="ID de la categoría"),
    tenant_id: str | None = Query(None, description="ID del tenant (para superadmin)"),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_tenant_db),
    empresa_from_header: Empresa | None = Depends(get_active_empresa)  # ✅ NUEVO
):
    """Calcula el siguiente número secuencial basado en el prefijo de la categoría."""
    # ✅ Usar empresa_id del header si no se pasó como query param
    empresa_id_final = empresa_id or (empresa_from_header.id if empresa_from_header else None)
    if not empresa_id_final:
        raise HTTPException(400, detail="Debe especificar una empresa (query param o header X-Company-Id)")
    
    await set_tenant_search_path(db, scope, tenant_id)
    
    stmt_cat = select(CategoriaActivoFijo).where(CategoriaActivoFijo.id == categoria_id)
    result_cat = await db.execute(stmt_cat)
    cat = result_cat.scalar_one_or_none()

    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    if not cat.codigo_prefijo:
        raise HTTPException(status_code=400, detail="La categoría no tiene un prefijo configurado")

    prefijo = cat.codigo_prefijo

    stmt_max = select(
        func.max(func.cast(func.split_part(ActivoFijo.codigo_interno, '-', 2), Integer))
    ).where(
        ActivoFijo.empresa_id == empresa_id_final,
        ActivoFijo.codigo_interno.like(f"{prefijo}-%")
    )

    result_max = await db.execute(stmt_max)
    max_num = result_max.scalar_one_or_none()

    siguiente_numero = (max_num or 0) + 1

    return {"siguiente_numero": siguiente_numero, "prefijo": prefijo}


@router.post("/depreciacion-mensual", response_model=ProcesarDepreciacionMensualResponse)
async def procesar_cierre_mensual(
    request: ProcesarDepreciacionMensualRequest,
    tenant_id: str | None = Query(None, description="ID del tenant (para superadmin)"),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_tenant_db),
    empresa_from_header: Empresa | None = Depends(get_active_empresa)  # ✅ NUEVO
):
    """Procesa la depreciación mensual consolidada."""
    # ✅ Sobrescribir empresa_id del payload con el del header si existe
    if empresa_from_header:
        request.empresa_id = empresa_from_header.id
    
    if not request.empresa_id:
        raise HTTPException(400, detail="Debe especificar una empresa (header X-Company-Id o en el payload)")
    
    await set_tenant_search_path(db, scope, tenant_id)
    return await activos_fijos_service.procesar_depreciacion_mensual_async(
        db=db,
        empresa_id=request.empresa_id,
        anio=request.anio_periodo,
        mes=request.mes_periodo
    )


# ==============================================================================
# RUTAS DINÁMICAS (DEBEN IR AL FINAL)
# ==============================================================================
@router.get("/", response_model=List[ActivoFijoResponse])
async def listar_activos(
    empresa_id: uuid.UUID = Depends(verificar_acceso_empresa),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_tenant_db)
):
    """Lista los activos fijos de una empresa."""
    stmt = select(ActivoFijo).options(
        selectinload(ActivoFijo.categoria),
        selectinload(ActivoFijo.cuenta_gasto),
        selectinload(ActivoFijo.cuenta_depreciacion_acumulada)
    ).where(
        ActivoFijo.empresa_id == empresa_id
    ).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{activo_id}", response_model=ActivoFijoResponse)
async def obtener_activo(
    activo_id: uuid.UUID,
    empresa_id: uuid.UUID = Depends(verificar_acceso_empresa),
    db: AsyncSession = Depends(get_tenant_db)
):
    """Obtiene los detalles de un activo fijo específico."""
    stmt = select(ActivoFijo).options(
        selectinload(ActivoFijo.categoria),
        selectinload(ActivoFijo.cuenta_gasto),
        selectinload(ActivoFijo.cuenta_depreciacion_acumulada)
    ).where(
        ActivoFijo.id == activo_id,
        ActivoFijo.empresa_id == empresa_id
    )
    result = await db.execute(stmt)
    activo = result.scalar_one_or_none()

    if not activo:
        raise HTTPException(status_code=404, detail="Activo fijo no encontrado")

    return activo


@router.post("/", response_model=ActivoFijoResponse, status_code=status.HTTP_201_CREATED)
async def crear_activo(
    data: ActivoFijoCreate,
    empresa_id: uuid.UUID = Depends(verificar_acceso_empresa),
    db: AsyncSession = Depends(get_tenant_db)
):
    """Registra un nuevo activo fijo."""
    return await activos_fijos_service.crear_activo_fijo_async(
        db=db,
        empresa_id=empresa_id,
        data=data
    )


@router.put("/{activo_id}", response_model=ActivoFijoResponse)
async def actualizar_activo(
    activo_id: uuid.UUID,
    data: ActivoFijoUpdate,
    empresa_id: uuid.UUID = Depends(verificar_acceso_empresa),
    db: AsyncSession = Depends(get_tenant_db)
):
    stmt = select(ActivoFijo).where(
        ActivoFijo.id == activo_id,
        ActivoFijo.empresa_id == empresa_id
    )
    result = await db.execute(stmt)
    activo_existente = result.scalar_one_or_none()
    if not activo_existente:
        raise HTTPException(status_code=404, detail="Activo fijo no encontrado o acceso denegado")

    return await activos_fijos_service.actualizar_activo_fijo_async(
        db=db, 
        activo_id=activo_id, 
        data=data
    )


@router.get("/{activo_id}/proyeccion", response_model=TablaDepreciacionProyectadaResponse)
async def obtener_proyeccion_depreciacion(
    activo_id: uuid.UUID,
    empresa_id: uuid.UUID = Depends(verificar_acceso_empresa),
    db: AsyncSession = Depends(get_tenant_db)
):
    """Genera la tabla de depreciación (histórico + proyección futura)."""
    stmt = select(ActivoFijo).where(
        ActivoFijo.id == activo_id,
        ActivoFijo.empresa_id == empresa_id
    )
    result = await db.execute(stmt)
    activo = result.scalar_one_or_none()

    if not activo:
        raise HTTPException(status_code=404, detail="Activo no encontrado o acceso denegado")

    return await activos_fijos_service.obtener_proyeccion_depreciacion_async(
        db=db, 
        activo_id=activo_id
    )