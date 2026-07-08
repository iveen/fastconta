"""Router para gestión de Secciones de Formulario SAT"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.sat.seccion import (
    SeccionFormularioCreate,
    SeccionFormularioDetail,
    SeccionFormularioListResponse,
    SeccionFormularioResponse,
    SeccionFormularioUpdate,
    SeccionReordenarRequest,
)
from app.services.sat.seccion_service import SeccionFormularioService

router = APIRouter(prefix="/secciones", tags=["Configuración Fiscal - Secciones"])


def get_service(db: AsyncSession = Depends(get_db)) -> SeccionFormularioService:
    return SeccionFormularioService(db)


# ============================================================
# LISTAR POR FORMULARIO
# ============================================================
@router.get("/", response_model=dict)
async def listar_secciones(
    formulario_id: UUID = Query(..., description="ID del formulario"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    service: SeccionFormularioService = Depends(get_service),
):
    """Lista secciones de un formulario ordenadas"""
    secciones, total = await service.obtener_por_formulario(
        formulario_id=formulario_id, skip=skip, limit=limit
    )
    return {
        "data": [SeccionFormularioListResponse.model_validate(s) for s in secciones],
        "total": total,
    }


# ============================================================
# OBTENER POR ID
# ============================================================
@router.get("/{seccion_id}", response_model=SeccionFormularioDetail)
async def obtener_seccion(
    seccion_id: UUID,
    service: SeccionFormularioService = Depends(get_service),
):
    """Obtiene una sección con sus casillas"""
    seccion = await service.obtener_por_id(seccion_id)
    if seccion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sección no encontrada",
        )
    return seccion


# ============================================================
# CREAR
# ============================================================
@router.post(
        "/", 
        response_model=SeccionFormularioResponse,
        status_code=status.HTTP_201_CREATED
)
async def crear_seccion(
    data: SeccionFormularioCreate,
    service: SeccionFormularioService = Depends(get_service),
):
    """Crea una nueva sección"""
    try:
        await service.verificar_editable(data.formulario_id)
        seccion = await service.crear(data.model_dump())
        return seccion
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================
# ACTUALIZAR
# ============================================================
@router.patch("/{seccion_id}", response_model=SeccionFormularioResponse)
async def actualizar_seccion(
    seccion_id: UUID,
    data: SeccionFormularioUpdate,
    service: SeccionFormularioService = Depends(get_service),
):
    """Actualiza una sección"""
    seccion = await service.actualizar(seccion_id, data.model_dump(exclude_unset=True))
    if seccion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sección no encontrada",
        )
    if seccion.es_automatica:
        raise HTTPException(status_code=403, detail="No se puede modificar una sección automática")

    return seccion


# ============================================================
# ELIMINAR
# ============================================================
@router.delete("/{seccion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_seccion(
    seccion_id: UUID,
    service: SeccionFormularioService = Depends(get_service),
):
    """Elimina una sección (cascade a casillas)"""
    seccion = await service.obtener_por_id(seccion_id)
    if seccion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sección no encontrada",
        )
    if seccion.es_automatica:
        raise HTTPException(status_code=403, detail="No se puede eliminar una sección automática")
    
    eliminado = await service.eliminar(seccion_id)
    if not eliminado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sección no encontrada",
        )


# ============================================================
# REORDENAR
# ============================================================
@router.post("/reordenar", status_code=status.HTTP_204_NO_CONTENT)
async def reordenar_secciones(
    data: SeccionReordenarRequest,
    formulario_id: UUID = Query(..., description="ID del formulario"),
    service: SeccionFormularioService = Depends(get_service),
):
    """Reordena las secciones de un formulario"""
    try:
        await service.reordenar(
            formulario_id=formulario_id,
            orden_secciones=data.orden_secciones,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))