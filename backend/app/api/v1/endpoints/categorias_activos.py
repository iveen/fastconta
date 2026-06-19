"""Endpoint para gestión de Categorías de Activos Fijos"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.configuracion_fiscal.categoria_activo import (
    CategoriaActivoFijoCreate,
    CategoriaActivoFijoListResponse,
    CategoriaActivoFijoResponse,
    CategoriaActivoFijoUpdate,
    CategoriaActivoImportResult,
)
from app.services.configuracion_fiscal.categoria_activo_service import (
    CategoriaActivoService,
)

router = APIRouter(
    prefix="/categorias-activos",
    tags=["Configuración Fiscal - Categorías Activos Fijos"],
)


def get_service(db: AsyncSession = Depends(get_db)) -> CategoriaActivoService:
    return CategoriaActivoService(db)


# ============================================================
# LISTAR
# ============================================================
@router.get("/", response_model=dict)
async def listar_categorias(
    is_active: bool | None = Query(None, description="Filtrar por estado activo"),
    search: str | None = Query(None, description="Buscar por nombre o prefijo"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: CategoriaActivoService = Depends(get_service),
):
    """Lista categorías de activos fijos con filtros y paginación"""
    categorias, total = await service.obtener_todos(
        is_active=is_active, search=search, skip=skip, limit=limit
    )
    return {
        "data": [CategoriaActivoFijoListResponse.model_validate(c) for c in categorias],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


# ============================================================
# LISTAR ACTIVAS (para dropdowns)
# ============================================================
@router.get("/activas", response_model=list[CategoriaActivoFijoListResponse])
async def listar_categorias_activas(
    service: CategoriaActivoService = Depends(get_service),
):
    """Lista todas las categorías activas (sin paginación, para dropdowns)"""
    return await service.obtener_todas_activas()


# ============================================================
# OBTENER POR ID
# ============================================================
@router.get("/{categoria_id}", response_model=CategoriaActivoFijoResponse)
async def obtener_categoria(
    categoria_id: str,
    service: CategoriaActivoService = Depends(get_service),
):
    """Obtiene una categoría por ID"""
    categoria = await service.obtener_por_id(categoria_id)
    if categoria is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada",
        )
    return categoria


# ============================================================
# CREAR
# ============================================================
@router.post("/", response_model=CategoriaActivoFijoResponse, status_code=status.HTTP_201_CREATED)
async def crear_categoria(
    data: CategoriaActivoFijoCreate,
    service: CategoriaActivoService = Depends(get_service),
):
    """Crea una nueva categoría de activo fijo"""
    try:
        categoria = await service.crear(data.model_dump())
        return categoria
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================
# ACTUALIZAR
# ============================================================
@router.patch("/{categoria_id}", response_model=CategoriaActivoFijoResponse)
async def actualizar_categoria(
    categoria_id: str,
    data: CategoriaActivoFijoUpdate,
    service: CategoriaActivoService = Depends(get_service),
):
    """Actualiza una categoría"""
    try:
        categoria = await service.actualizar(
            categoria_id, data.model_dump(exclude_unset=True)
        )
        if categoria is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoría no encontrada",
            )
        return categoria
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================
# ELIMINAR (soft delete)
# ============================================================
@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_categoria(
    categoria_id: str,
    service: CategoriaActivoService = Depends(get_service),
):
    """Desactiva una categoría (soft delete)"""
    eliminado = await service.eliminar(categoria_id)
    if not eliminado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada",
        )


# ============================================================
# EXPORTAR EXCEL
# ============================================================
@router.get("/exportar/excel")
async def exportar_excel(
    service: CategoriaActivoService = Depends(get_service),
):
    """Exporta catálogo de categorías a Excel"""
    archivo = await service.exportar_excel()

    return StreamingResponse(
        archivo,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=categorias_activos_fijos.xlsx"},
    )


# ============================================================
# IMPORTAR EXCEL
# ============================================================
@router.post("/importar/excel", response_model=CategoriaActivoImportResult)
async def importar_excel(
    archivo: UploadFile,
    sobrescribir: bool = Query(False, description="Si es True, actualiza registros existentes"),
    service: CategoriaActivoService = Depends(get_service),
):
    """
    Importa categorías desde Excel.

    El archivo debe tener las columnas:
    nombre, tasa_minima_anual, tasa_maxima_anual, vida_util_meses_default, codigo_prefijo, descripcion (opcional)
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