"""Router para Configuración Régimen-DTE"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.configuracion_fiscal.tipo_dte import (
    RegimenDteBulkRequest,
    RegimenDteConfigCreate,
    RegimenDteConfigResponse,
    RegimenDteConfigUpdate,
)
from app.services.configuracion_fiscal.regimen_dte_service import RegimenDteService

router = APIRouter(
    prefix="/regimen-dte-config",
    tags=["Configuración Fiscal - Régimen DTE"],
)


def get_service(db: AsyncSession = Depends(get_db)) -> RegimenDteService:
    return RegimenDteService(db)


# ============================================================
# LISTAR POR RÉGIMEN
# ============================================================
@router.get("/regimen/{regimen_id}", response_model=list[RegimenDteConfigResponse])
async def listar_por_regimen(
    regimen_id: UUID,
    service: RegimenDteService = Depends(get_service),
):
    """Lista DTE configurados para un régimen"""
    return await service.obtener_por_regimen(regimen_id)


# ============================================================
# LISTAR POR DTE
# ============================================================
@router.get("/dte/{dte_id}", response_model=list[RegimenDteConfigResponse])
async def listar_por_dte(
    dte_id: UUID,
    service: RegimenDteService = Depends(get_service),
):
    """Lista regímenes configurados para un DTE"""
    return await service.obtener_por_dte(dte_id)


# ============================================================
# DTE PERMITIDOS PARA RÉGIMEN
# ============================================================
@router.get("/regimen/{regimen_id}/dte-permitidos")
async def obtener_dte_permitidos(
    regimen_id: UUID,
    service: RegimenDteService = Depends(get_service),
):
    """Obtiene los DTE permitidos para un régimen"""
    return await service.obtener_dte_permitidos(regimen_id)


# ============================================================
# ASOCIAR DTE A RÉGIMEN
# ============================================================
@router.post(
    "/regimen/{regimen_id}/dte",
    response_model=RegimenDteConfigResponse,
    status_code=status.HTTP_201_CREATED,
)
async def asociar_dte(
    regimen_id: UUID,
    data: RegimenDteConfigCreate,
    service: RegimenDteService = Depends(get_service),
):
    """Asocia un DTE a un régimen"""
    try:
        config = await service.asociar(
            regimen_id=regimen_id,
            dte_id=data.dte_id,
            es_exclusivo=data.es_exclusivo,
        )
        return config
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================
# ACTUALIZAR CONFIGURACIÓN
# ============================================================
@router.patch(
    "/regimen/{regimen_id}/dte/{dte_id}",
    response_model=RegimenDteConfigResponse,
)
async def actualizar_configuracion(
    regimen_id: UUID,
    dte_id: UUID,
    data: RegimenDteConfigUpdate,
    service: RegimenDteService = Depends(get_service),
):
    """Actualiza la configuración entre régimen y DTE"""
    config = await service.actualizar_configuracion(
        regimen_id=regimen_id,
        dte_id=dte_id,
        es_exclusivo=data.es_exclusivo,
    )
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración no encontrada",
        )
    return config


# ============================================================
# DESASOCIAR DTE
# ============================================================
@router.delete(
    "/regimen/{regimen_id}/dte/{dte_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def desasociar_dte(
    regimen_id: UUID,
    dte_id: UUID,
    service: RegimenDteService = Depends(get_service),
):
    """Elimina la asociación entre régimen y DTE"""
    eliminado = await service.desasociar(regimen_id, dte_id)
    if not eliminado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración no encontrada",
        )


# ============================================================
# ASOCIAR BULK
# ============================================================
@router.post(
    "/regimen/{regimen_id}/dte/bulk",
    response_model=list[RegimenDteConfigResponse],
    status_code=status.HTTP_201_CREATED,
)
async def asociar_dte_bulk(
    regimen_id: UUID,
    data: RegimenDteBulkRequest,
    service: RegimenDteService = Depends(get_service),
):
    """Asocia múltiples DTE a un régimen"""
    try:
        configs = await service.asociar_bulk(
            regimen_id=regimen_id,
            dte_ids=data.dte_ids,
            es_exclusivo=data.es_exclusivo,
        )
        return configs
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))