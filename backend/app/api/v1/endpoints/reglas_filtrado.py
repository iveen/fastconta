"""Endpoint para gestión de Reglas de Filtrado y Exclusiones"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.configuracion_fiscal.regla_filtrado import (
    CasillaConfigResponse,
    ExclusionCreate,
    ExclusionListResponse,
    ExclusionResponse,
    ExclusionUpdate,
    ReglaFiltradoCreate,
    ReglaFiltradoListResponse,
    ReglaFiltradoResponse,
    ReglaFiltradoUpdate,
)
from app.services.configuracion_fiscal.regla_filtrado_service import (
    ReglaFiltradoService,
)

router = APIRouter(
    prefix="/reglas-filtrado",
    tags=["Configuración Fiscal - Reglas y Exclusiones"],
)


def get_service(db: AsyncSession = Depends(get_db)) -> ReglaFiltradoService:
    return ReglaFiltradoService(db)


# ============================================================
# CONFIGURACIÓN COMPLETA DE CASILLA
# ============================================================
@router.get("/casilla/{casilla_id}", response_model=CasillaConfigResponse)
async def obtener_configuracion_casilla(
    casilla_id: UUID,
    service: ReglaFiltradoService = Depends(get_service),
):
    """Obtiene la configuración completa de una casilla (reglas + exclusiones)"""
    config = await service.obtener_configuracion_casilla(casilla_id)
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Casilla no encontrada",
        )
    return config


# ============================================================
# LISTAR REGLAS
# ============================================================
@router.get("/reglas", response_model=dict)
async def listar_reglas(
    casilla_id: UUID | None = Query(None, description="Filtrar por casilla"),
    es_activa: bool | None = Query(None, description="Filtrar por estado activo"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: ReglaFiltradoService = Depends(get_service),
):
    """Lista reglas de filtrado con filtros y paginación"""
    reglas, total = await service.obtener_todas_reglas(
        casilla_id=casilla_id, es_activa=es_activa, skip=skip, limit=limit
    )
    return {
        "data": [ReglaFiltradoListResponse.model_validate(r) for r in reglas],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


# ============================================================
# OBTENER REGLA POR ID
# ============================================================
@router.get("/reglas/{regla_id}", response_model=ReglaFiltradoResponse)
async def obtener_regla(
    regla_id: UUID,
    service: ReglaFiltradoService = Depends(get_service),
):
    """Obtiene una regla específica"""
    regla = await service.obtener_regla_por_id(regla_id)
    if regla is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Regla no encontrada",
        )
    return regla


# ============================================================
# CREAR REGLA
# ============================================================
@router.post("/reglas", response_model=ReglaFiltradoResponse, status_code=status.HTTP_201_CREATED)
async def crear_regla(
    data: ReglaFiltradoCreate,
    service: ReglaFiltradoService = Depends(get_service),
):
    """Crea una nueva regla de filtrado"""
    try:
        regla = await service.crear_regla(data.model_dump())
        return regla
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================
# ACTUALIZAR REGLA
# ============================================================
@router.patch("/reglas/{regla_id}", response_model=ReglaFiltradoResponse)
async def actualizar_regla(
    regla_id: UUID,
    data: ReglaFiltradoUpdate,
    service: ReglaFiltradoService = Depends(get_service),
):
    """Actualiza una regla"""
    regla = await service.actualizar_regla(regla_id, data.model_dump(exclude_unset=True))
    if regla is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Regla no encontrada",
        )
    return regla


# ============================================================
# ELIMINAR REGLA
# ============================================================
@router.delete("/reglas/{regla_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_regla(
    regla_id: UUID,
    service: ReglaFiltradoService = Depends(get_service),
):
    """Elimina una regla"""
    eliminado = await service.eliminar_regla(regla_id)
    if not eliminado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Regla no encontrada",
        )


# ============================================================
# LISTAR EXCLUSIONES
# ============================================================
@router.get("/exclusiones", response_model=dict)
async def listar_exclusiones(
    casilla_id: UUID | None = Query(None, description="Filtrar por casilla"),
    es_activa: bool | None = Query(None, description="Filtrar por estado activo"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: ReglaFiltradoService = Depends(get_service),
):
    """Lista exclusiones con filtros y paginación"""
    exclusiones, total = await service.obtener_todas_exclusiones(
        casilla_id=casilla_id, es_activa=es_activa, skip=skip, limit=limit
    )
    return {
        "data": [ExclusionListResponse.model_validate(e) for e in exclusiones],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


# ============================================================
# OBTENER EXCLUSIÓN POR ID
# ============================================================
@router.get("/exclusiones/{exclusion_id}", response_model=ExclusionResponse)
async def obtener_exclusion(
    exclusion_id: UUID,
    service: ReglaFiltradoService = Depends(get_service),
):
    """Obtiene una exclusión específica"""
    exclusion = await service.obtener_exclusion_por_id(exclusion_id)
    if exclusion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exclusión no encontrada",
        )
    return exclusion


# ============================================================
# CREAR EXCLUSIÓN
# ============================================================
@router.post("/exclusiones", response_model=ExclusionResponse, status_code=status.HTTP_201_CREATED)
async def crear_exclusion(
    data: ExclusionCreate,
    service: ReglaFiltradoService = Depends(get_service),
):
    """Crea una nueva exclusión"""
    try:
        exclusion = await service.crear_exclusion(data.model_dump())
        return exclusion
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================
# ACTUALIZAR EXCLUSIÓN
# ============================================================
@router.patch("/exclusiones/{exclusion_id}", response_model=ExclusionResponse)
async def actualizar_exclusion(
    exclusion_id: UUID,
    data: ExclusionUpdate,
    service: ReglaFiltradoService = Depends(get_service),
):
    """Actualiza una exclusión"""
    exclusion = await service.actualizar_exclusion(
        exclusion_id, data.model_dump(exclude_unset=True)
    )
    if exclusion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exclusión no encontrada",
        )
    return exclusion


# ============================================================
# ELIMINAR EXCLUSIÓN
# ============================================================
@router.delete("/exclusiones/{exclusion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_exclusion(
    exclusion_id: UUID,
    service: ReglaFiltradoService = Depends(get_service),
):
    """Elimina una exclusión"""
    eliminado = await service.eliminar_exclusion(exclusion_id)
    if not eliminado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exclusión no encontrada",
        )