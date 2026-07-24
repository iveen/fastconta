"""Router para gestión de Tipos DTE"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.sat.tipo_dte import (
    TipoDTECreate,
    TipoDTEImportResult,
    TipoDTEListResponse,
    TipoDTEResponse,
    TipoDTEUpdate,
)
from app.services.sat.tipo_dte_service import TipoDTEService

router = APIRouter(prefix="/tipos-dte", tags=["Configuración Fiscal - Tipos DTE"])
logger = logging.getLogger(__name__)


def get_service(db: AsyncSession = Depends(get_db)) -> TipoDTEService:
    return TipoDTEService(db)


# ============================================================
# LISTAR
# ============================================================
@router.get("/", response_model=dict)
async def listar_tipos_dte(
    activo: bool | None = Query(None, description="Filtrar por estado activo"),
    es_factura: bool | None = Query(None, description="Filtrar si es factura"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: TipoDTEService = Depends(get_service),
):
    """Lista tipos DTE con filtros y paginación"""
    dtes, total = await service.obtener_todos(
        activo=activo, es_factura=es_factura, skip=skip, limit=limit
    )
    return {
        "data": [TipoDTEListResponse.model_validate(d).model_dump() for d in dtes],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


# ============================================================
# LISTAR ACTIVOS (para dropdowns)
# ============================================================
@router.get("/activos", response_model=list[TipoDTEListResponse])
async def listar_tipos_dte_activos(
    service: TipoDTEService = Depends(get_service),
):
    """Lista todos los tipos DTE activos (sin paginación, para dropdowns)"""
    return await service.obtener_todos_activos()


# ============================================================
# OBTENER POR ID
# ============================================================
@router.get("/{dte_id}", response_model=TipoDTEResponse)
async def obtener_tipo_dte(
    dte_id: int,  # ✅ BIGINT (era UUID)
    service: TipoDTEService = Depends(get_service),
):
    """Obtiene un tipo DTE por ID"""
    dte = await service.obtener_por_id(dte_id)
    if dte is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo DTE no encontrado",
        )
    return dte


# ============================================================
# CREAR
# ============================================================
@router.post("/", response_model=TipoDTEResponse, status_code=status.HTTP_201_CREATED)
async def crear_tipo_dte(
    data: TipoDTECreate,
    service: TipoDTEService = Depends(get_service),
):
    """Crea un nuevo tipo DTE"""
    try:
        dte = await service.crear(data.model_dump())
        return dte
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================
# ACTUALIZAR
# ============================================================
@router.patch("/{dte_id}", response_model=TipoDTEResponse)
async def actualizar_tipo_dte(
    dte_id: int,  # ✅ BIGINT (era UUID)
    data: TipoDTEUpdate,
    service: TipoDTEService = Depends(get_service),
):
    """Actualiza un tipo DTE"""
    dte = await service.actualizar(dte_id, data.model_dump(exclude_unset=True))
    if dte is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo DTE no encontrado",
        )
    return dte


# ============================================================
# ELIMINAR (soft delete)
# ============================================================
@router.delete("/{dte_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_tipo_dte(
    dte_id: int,  # ✅ BIGINT (era UUID)
    service: TipoDTEService = Depends(get_service),
):
    """Desactiva un tipo DTE (soft delete)"""
    eliminado = await service.eliminar(dte_id)
    if not eliminado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo DTE no encontrado",
        )


# ============================================================
# EXPORTAR EXCEL
# ============================================================
@router.get("/exportar/excel")
async def exportar_excel(
    service: TipoDTEService = Depends(get_service),
):
    """Exporta catálogo de tipos DTE a Excel"""
    archivo = await service.exportar_excel()
    return StreamingResponse(
        archivo,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=tipos_dte.xlsx"},
    )


# ============================================================
# IMPORTAR EXCEL
# ============================================================
@router.post("/importar/excel", response_model=TipoDTEImportResult)
async def importar_excel(
    archivo: UploadFile,
    sobrescribir: bool = Query(False, description="Si es True, actualiza registros existentes"),
    service: TipoDTEService = Depends(get_service),
):
    """
    Importa tipos DTE desde Excel.
    El archivo debe tener las columnas: codigo, descripcion, requiere_complemento, es_factura
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