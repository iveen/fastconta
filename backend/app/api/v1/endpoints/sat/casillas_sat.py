"""Router para gestión de Casillas SAT"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.sat.casilla import (
    CasillaSatCreate,
    CasillaSatDetail,
    CasillaSatDuplicarRequest,
    CasillaSatListResponse,
    CasillaSatResponse,
    CasillaSatUpdate,
)
from app.services.sat.casilla_service import CasillaSatService

router = APIRouter(prefix="/casillas", tags=["Configuración Fiscal - Casillas"])


def get_service(db: AsyncSession = Depends(get_db)) -> CasillaSatService:
    return CasillaSatService(db)


# ============================================================
# LISTAR POR SECCIÓN
# ============================================================
@router.get("/", response_model=dict)
async def listar_casillas(
    seccion_id: UUID = Query(..., description="ID de la sección"),
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
    service: CasillaSatService = Depends(get_service),
):
    """Lista casillas de una sección"""
    casillas, total = await service.obtener_por_seccion(
        seccion_id=seccion_id, skip=skip, limit=limit
    )
    return {
        "data": [CasillaSatListResponse.model_validate(c) for c in casillas],
        "total": total,
    }


# ============================================================
# OBTENER POR ID
# ============================================================
@router.get("/{casilla_id}", response_model=CasillaSatDetail)
async def obtener_casilla(
    casilla_id: UUID,
    service: CasillaSatService = Depends(get_service),
):
    """Obtiene una casilla con reglas y exclusiones"""
    casilla = await service.obtener_por_id(casilla_id)
    if casilla is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Casilla no encontrada",
        )
    return casilla


# ============================================================
# CREAR
# ============================================================
@router.post("/", response_model=CasillaSatResponse, status_code=status.HTTP_201_CREATED)
async def crear_casilla(
    data: CasillaSatCreate,
    service: CasillaSatService = Depends(get_service),
):
    """Crea una nueva casilla"""
    try:
        await service.verificar_editable(data.seccion_id)
        casilla = await service.crear(data.model_dump())
        return casilla
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================
# ACTUALIZAR
# ============================================================
@router.patch("/{casilla_id}", response_model=CasillaSatResponse)
async def actualizar_casilla(
    casilla_id: UUID,
    data: CasillaSatUpdate,
    service: CasillaSatService = Depends(get_service),
):
    """Actualiza una casilla"""
    casilla = await service.obtener_por_id(casilla_id)

    if casilla is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Casilla no encontrada",
        )
    
    if casilla.es_automatica:
        raise HTTPException(status_code=403, detail="No se puede modificar una casilla automática")
    
    casilla = await service.actualizar(casilla_id, data.model_dump(exclude_unset=True))

    return casilla


# ============================================================
# ELIMINAR
# ============================================================
@router.delete("/{casilla_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_casilla(
    casilla_id: UUID,
    service: CasillaSatService = Depends(get_service),
):
    """Elimina una casilla (cascade a reglas y exclusiones)"""
    casilla = await service.obtener_por_id(casilla_id)

    if casilla is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Casilla no encontrada",
        )
    
    if casilla.es_automatica:
        raise HTTPException(status_code=403, detail="No se puede eliminar una casilla automática")

    eliminado = await service.eliminar(casilla_id)
    if not eliminado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Casilla no encontrada",
        )


# ============================================================
# DUPLICAR
# ============================================================
@router.post("/{casilla_id}/duplicar", response_model=CasillaSatResponse)
async def duplicar_casilla(
    casilla_id: UUID,
    data: CasillaSatDuplicarRequest,
    service: CasillaSatService = Depends(get_service),
):
    """Duplica una casilla con sus reglas y exclusiones"""
    try:
        nueva = await service.duplicar(
            casilla_id=casilla_id,
            nuevo_codigo=data.nuevo_codigo,
            nuevo_nombre=data.nuevo_nombre,
            copiar_reglas=data.copiar_reglas,
            copiar_exclusiones=data.copiar_exclusiones,
        )
        return nueva
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))