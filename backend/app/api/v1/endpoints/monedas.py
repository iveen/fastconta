"""Endpoint para gestión de Catálogo de Monedas"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.configuracion_fiscal.moneda import (
    CatalogoMonedaCreate,
    CatalogoMonedaImportResult,
    CatalogoMonedaListResponse,
    CatalogoMonedaResponse,
    CatalogoMonedaUpdate,
)
from app.services.configuracion_fiscal.moneda_service import CatalogoMonedaService

router = APIRouter(
    prefix="/monedas",
    tags=["Configuración Fiscal - Catálogo de Monedas"],
)


def get_service(db: AsyncSession = Depends(get_db)) -> CatalogoMonedaService:
    return CatalogoMonedaService(db)


# ============================================================
# LISTAR
# ============================================================
@router.get("/", response_model=dict)
async def listar_monedas(
    activo: bool | None = Query(None, description="Filtrar por estado activo"),
    search: str | None = Query(
        None, description="Buscar por nombre, código ISO o Banguat"
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: CatalogoMonedaService = Depends(get_service),
):
    """Lista monedas con filtros y paginación"""
    monedas, total = await service.obtener_todos(
        activo=activo, search=search, skip=skip, limit=limit
    )
    return {
        "data": [CatalogoMonedaListResponse.model_validate(m) for m in monedas],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


# ============================================================
# LISTAR ACTIVAS (para dropdowns)
# ============================================================
@router.get("/activas", response_model=list[CatalogoMonedaListResponse])
async def listar_monedas_activas(
    service: CatalogoMonedaService = Depends(get_service),
):
    """Lista todas las monedas activas (sin paginación, para dropdowns)"""
    return await service.obtener_todas_activas()


# ============================================================
# OBTENER POR ID
# ============================================================
@router.get("/{moneda_id}", response_model=CatalogoMonedaResponse)
async def obtener_moneda(
    moneda_id: UUID,
    service: CatalogoMonedaService = Depends(get_service),
):
    """Obtiene una moneda por ID"""
    moneda = await service.obtener_por_id(moneda_id)
    if moneda is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Moneda no encontrada",
        )
    return moneda


# ============================================================
# CREAR
# ============================================================
@router.post("/", response_model=CatalogoMonedaResponse, status_code=status.HTTP_201_CREATED)
async def crear_moneda(
    data: CatalogoMonedaCreate,
    service: CatalogoMonedaService = Depends(get_service),
):
    """Crea una nueva moneda"""
    try:
        moneda = await service.crear(data.model_dump())
        return moneda
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================
# ACTUALIZAR
# ============================================================
@router.patch("/{moneda_id}", response_model=CatalogoMonedaResponse)
async def actualizar_moneda(
    moneda_id: UUID,
    data: CatalogoMonedaUpdate,
    service: CatalogoMonedaService = Depends(get_service),
):
    """Actualiza una moneda"""
    try:
        moneda = await service.actualizar(
            moneda_id, data.model_dump(exclude_unset=True)
        )
        if moneda is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Moneda no encontrada",
            )
        return moneda
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================
# ELIMINAR (soft delete)
# ============================================================
@router.delete("/{moneda_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_moneda(
    moneda_id: UUID,
    service: CatalogoMonedaService = Depends(get_service),
):
    """Desactiva una moneda (soft delete)"""
    eliminado = await service.eliminar(moneda_id)
    if not eliminado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Moneda no encontrada",
        )


# ============================================================
# EXPORTAR EXCEL
# ============================================================
@router.get("/exportar/excel")
async def exportar_excel(
    service: CatalogoMonedaService = Depends(get_service),
):
    """Exporta catálogo de monedas a Excel"""
    archivo = await service.exportar_excel()

    return StreamingResponse(
        archivo,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=monedas.xlsx"},
    )


# ============================================================
# IMPORTAR EXCEL
# ============================================================
@router.post("/importar/excel", response_model=CatalogoMonedaImportResult)
async def importar_excel(
    archivo: UploadFile,
    sobrescribir: bool = Query(
        False, description="Si es True, actualiza registros existentes"
    ),
    service: CatalogoMonedaService = Depends(get_service),
):
    """
    Importa monedas desde Excel.

    El archivo debe tener las columnas:
    codigo_banguat, codigo_iso, nombre, simbolo (opcional), decimales (opcional, default 2)
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