"""Endpoint para gestión de Mapeo Casilla-Cuenta"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.sat.mapeo_casilla import (
    MapeoCasillaCuentaCreate,
    MapeoCasillaCuentaListResponse,
    MapeoCasillaCuentaResponse,
    MapeoCasillaCuentaUpdate,
    MapeoImportResult,
)
from app.services.sat.mapeo_casilla_service import (
    MapeoCasillaCuentaService,
)

router = APIRouter(
    prefix="/mapeo-casilla-cuenta",
    tags=["Configuración Fiscal - Mapeo Contable"],
)


def get_service(db: AsyncSession = Depends(get_db)) -> MapeoCasillaCuentaService:
    return MapeoCasillaCuentaService(db)


# ============================================================
# LISTAR
# ============================================================
@router.get("/", response_model=dict)
async def listar_mapeos(
    casilla_id: UUID | None = Query(None, description="Filtrar por casilla"),
    tenant_id: UUID | None = Query(None, description="Filtrar por tenant (NULL = globales)"),
    empresa_id: UUID | None = Query(None, description="Filtrar por empresa (NULL = globales)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: MapeoCasillaCuentaService = Depends(get_service),
):
    """Lista mapeos contables con filtros"""
    mapeos, total = await service.obtener_todos(
        casilla_id=casilla_id, tenant_id=tenant_id, empresa_id=empresa_id, skip=skip, limit=limit
    )
    return {
        "data": [MapeoCasillaCuentaListResponse.model_validate(m) for m in mapeos],
        "total": total,
    }


# ============================================================
# OBTENER POR ID
# ============================================================
@router.get("/{mapeo_id}", response_model=MapeoCasillaCuentaResponse)
async def obtener_mapeo(
    mapeo_id: UUID,
    service: MapeoCasillaCuentaService = Depends(get_service),
):
    """Obtiene un mapeo específico"""
    mapeo = await service.obtener_por_id(mapeo_id)
    if mapeo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapeo no encontrado")
    return mapeo


# ============================================================
# CREAR
# ============================================================
@router.post("/", response_model=MapeoCasillaCuentaResponse, status_code=status.HTTP_201_CREATED)
async def crear_mapeo(
    data: MapeoCasillaCuentaCreate,
    service: MapeoCasillaCuentaService = Depends(get_service),
):
    """Crea un nuevo mapeo casilla-cuenta"""
    try:
        return await service.crear(data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================
# ACTUALIZAR
# ============================================================
@router.patch("/{mapeo_id}", response_model=MapeoCasillaCuentaResponse)
async def actualizar_mapeo(
    mapeo_id: UUID,
    data: MapeoCasillaCuentaUpdate,
    service: MapeoCasillaCuentaService = Depends(get_service),
):
    """Actualiza un mapeo"""
    try:
        mapeo = await service.actualizar(mapeo_id, data.model_dump(exclude_unset=True))
        if mapeo is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapeo no encontrado")
        return mapeo
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================
# ELIMINAR
# ============================================================
@router.delete("/{mapeo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_mapeo(
    mapeo_id: UUID,
    service: MapeoCasillaCuentaService = Depends(get_service),
):
    """Elimina un mapeo"""
    eliminado = await service.eliminar(mapeo_id)
    if not eliminado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapeo no encontrado")


# ============================================================
# EXPORTAR EXCEL
# ============================================================
@router.get("/exportar/excel")
async def exportar_excel(
    tenant_id: UUID | None = Query(None, description="Exportar mapeos de un tenant específico"),
    empresa_id: UUID | None = Query(None, description="Exportar mapeos de una empresa específica"),
    service: MapeoCasillaCuentaService = Depends(get_service),
):
    """Exporta mapeo contable a Excel"""
    archivo = await service.exportar_excel(tenant_id=tenant_id, empresa_id=empresa_id)

    return StreamingResponse(
        archivo,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=mapeo_casilla_cuenta.xlsx"},
    )


# ============================================================
# IMPORTAR EXCEL
# ============================================================
@router.post("/importar/excel", response_model=MapeoImportResult)
async def importar_excel(
    archivo: UploadFile,
    sobrescribir: bool = Query(False, description="Si es True, actualiza registros existentes"),
    tenant_id: UUID | None = Query(None, description="Tenant al que se asignarán los mapeos"),
    service: MapeoCasillaCuentaService = Depends(get_service),
):
    """
    Importa mapeos desde Excel.
    
    Columnas requeridas: codigo_casilla, codigo_cuenta_sugerido, nombre_cuenta_sugerido, tipo_movimiento
    Columna opcional: ambito (GLOBAL, TENANT, EMPRESA)
    """
    if not archivo.filename or not archivo.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se aceptan archivos Excel (.xlsx, .xls)",
        )

    contenido = await archivo.read()

    try:
        return await service.importar_excel(
            archivo_bytes=contenido,
            tenant_id=tenant_id,
            sobrescribir=sobrescribir,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))