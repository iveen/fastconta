"""Endpoint para gestión de Actividades Económicas SAT"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.configuracion_fiscal.actividad_economica import (
    ActividadEconomicaCreate,
    ActividadEconomicaImportResult,
    ActividadEconomicaListResponse,
    ActividadEconomicaResponse,
    ActividadEconomicaUpdate,
)
from app.services.configuracion_fiscal.actividad_economica_service import (
    ActividadEconomicaService,
)

router = APIRouter(
    prefix="/actividades-economicas",
    tags=["Configuración Fiscal - Actividades Económicas"],
)


def get_service(db: AsyncSession = Depends(get_db)) -> ActividadEconomicaService:
    return ActividadEconomicaService(db)


# ============================================================
# LISTAR
# ============================================================
@router.get("/", response_model=dict)
async def listar_actividades(
    activa: bool | None = Query(None, description="Filtrar por estado activo"),
    seccion: str | None = Query(None, description="Filtrar por sección"),
    search: str | None = Query(None, description="Buscar por código o nombre"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: ActividadEconomicaService = Depends(get_service),
):
    """Lista actividades económicas con filtros y paginación"""
    actividades, total = await service.obtener_todos(
        activa=activa, seccion=seccion, search=search, skip=skip, limit=limit
    )
    return {
        "data": [ActividadEconomicaListResponse.model_validate(a) for a in actividades],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


# ============================================================
# LISTAR ACTIVAS (para dropdowns)
# ============================================================
@router.get("/activas", response_model=list[ActividadEconomicaListResponse])
async def listar_actividades_activas(
    service: ActividadEconomicaService = Depends(get_service),
):
    """Lista todas las actividades económicas activas (sin paginación, para dropdowns)"""
    return await service.obtener_todas_activas()


# ============================================================
# SECCIONES ÚNICAS
# ============================================================
@router.get("/secciones", response_model=list[str])
async def obtener_secciones(
    service: ActividadEconomicaService = Depends(get_service),
):
    """Obtiene lista de secciones únicas (para filtros)"""
    return await service.obtener_secciones_unicas()


# ============================================================
# OBTENER POR ID
# ============================================================
@router.get("/{actividad_id}", response_model=ActividadEconomicaResponse)
async def obtener_actividad(
    actividad_id: UUID,
    service: ActividadEconomicaService = Depends(get_service),
):
    """Obtiene una actividad económica por ID"""
    actividad = await service.obtener_por_id(actividad_id)
    if actividad is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actividad económica no encontrada",
        )
    return actividad


# ============================================================
# CREAR
# ============================================================
@router.post("/", response_model=ActividadEconomicaResponse, status_code=status.HTTP_201_CREATED)
async def crear_actividad(
    data: ActividadEconomicaCreate,
    service: ActividadEconomicaService = Depends(get_service),
):
    """Crea una nueva actividad económica"""
    try:
        actividad = await service.crear(data.model_dump())
        return actividad
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================
# ACTUALIZAR
# ============================================================
@router.patch("/{actividad_id}", response_model=ActividadEconomicaResponse)
async def actualizar_actividad(
    actividad_id: UUID,
    data: ActividadEconomicaUpdate,
    service: ActividadEconomicaService = Depends(get_service),
):
    """Actualiza una actividad económica"""
    actividad = await service.actualizar(actividad_id, data.model_dump(exclude_unset=True))
    if actividad is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actividad económica no encontrada",
        )
    return actividad


# ============================================================
# ELIMINAR (soft delete)
# ============================================================
@router.delete("/{actividad_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_actividad(
    actividad_id: UUID,
    service: ActividadEconomicaService = Depends(get_service),
):
    """Desactiva una actividad económica (soft delete)"""
    eliminado = await service.eliminar(actividad_id)
    if not eliminado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actividad económica no encontrada",
        )


# ============================================================
# EXPORTAR EXCEL
# ============================================================
@router.get("/exportar/excel")
async def exportar_excel(
    service: ActividadEconomicaService = Depends(get_service),
):
    """Exporta catálogo de actividades económicas a Excel"""
    archivo = await service.exportar_excel()
    
    return StreamingResponse(
        archivo,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=actividades_economicas.xlsx"},
    )


# ============================================================
# IMPORTAR EXCEL
# ============================================================
@router.post("/importar/excel", response_model=ActividadEconomicaImportResult)
async def importar_excel(
    archivo: UploadFile,
    sobrescribir: bool = Query(False, description="Si es True, actualiza registros existentes"),
    service: ActividadEconomicaService = Depends(get_service),
):
    """
    Importa actividades económicas desde Excel.
    
    El archivo debe tener las columnas: codigo_sat, nombre_actividad, seccion (opcional)
    """
    if not archivo.filename or not archivo.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se aceptan archivos Excel (.xlsx, .xls)",
        )

    contenido = await archivo.read()
    
    try:
        resultado = await service.importar_excel(
            archivo_bytes=contenido,
            sobrescribir=sobrescribir,
        )
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))