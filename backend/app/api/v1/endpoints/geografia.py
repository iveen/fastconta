"""Endpoint para gestión de Geografía (Departamentos y Municipios)"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.configuracion_fiscal.geografia import (
    DepartamentoConMunicipiosResponse,
    DepartamentoCreate,
    DepartamentoListResponse,
    DepartamentoResponse,
    DepartamentoUpdate,
    GeografiaImportResult,
    MunicipioCreate,
    MunicipioListResponse,
    MunicipioResponse,
    MunicipioUpdate,
)
from app.services.configuracion_fiscal.geografia_service import GeografiaService

router = APIRouter(
    prefix="/geografia",
    tags=["Configuración Fiscal - Geografía"],
)


def get_service(db: AsyncSession = Depends(get_db)) -> GeografiaService:
    return GeografiaService(db)


# ============================================================
# DEPARTAMENTOS
# ============================================================

@router.get("/departamentos", response_model=dict)
async def listar_departamentos(
    search: str | None = Query(None, description="Buscar por nombre o código"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: GeografiaService = Depends(get_service),
):
    """Lista departamentos con conteo de municipios"""
    deptos, total = await service.obtener_departamentos(
        search=search, skip=skip, limit=limit
    )
    return {
        "data": [DepartamentoListResponse.model_validate(d) for d in deptos],
        "total": total,
    }


@router.get("/departamentos/todos", response_model=list[DepartamentoListResponse])
async def listar_todos_departamentos(
    service: GeografiaService = Depends(get_service),
):
    """Lista todos los departamentos (sin paginación, para dropdowns)"""
    return await service.obtener_todos_departamentos()


@router.get("/departamentos/{departamento_id}", response_model=DepartamentoConMunicipiosResponse)
async def obtener_departamento(
    departamento_id: UUID,
    service: GeografiaService = Depends(get_service),
):
    """Obtiene un departamento con sus municipios"""
    depto = await service.obtener_departamento_por_id(departamento_id)
    if depto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Departamento no encontrado",
        )
    return depto


@router.post("/departamentos", response_model=DepartamentoResponse, status_code=status.HTTP_201_CREATED)
async def crear_departamento(
    data: DepartamentoCreate,
    service: GeografiaService = Depends(get_service),
):
    """Crea un nuevo departamento"""
    try:
        depto = await service.crear_departamento(data.model_dump())
        return depto
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/departamentos/{departamento_id}", response_model=DepartamentoResponse)
async def actualizar_departamento(
    departamento_id: UUID,
    data: DepartamentoUpdate,
    service: GeografiaService = Depends(get_service),
):
    """Actualiza un departamento"""
    depto = await service.actualizar_departamento(
        departamento_id, data.model_dump(exclude_unset=True)
    )
    if depto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Departamento no encontrado",
        )
    return depto


@router.delete("/departamentos/{departamento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_departamento(
    departamento_id: UUID,
    service: GeografiaService = Depends(get_service),
):
    """Elimina un departamento (cascade a municipios)"""
    eliminado = await service.eliminar_departamento(departamento_id)
    if not eliminado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Departamento no encontrado",
        )


# ============================================================
# MUNICIPIOS
# ============================================================

@router.get("/municipios", response_model=dict)
async def listar_municipios(
    departamento_id: UUID | None = Query(None, description="Filtrar por departamento"),
    search: str | None = Query(None, description="Buscar por nombre o código"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: GeografiaService = Depends(get_service),
):
    """Lista municipios con filtros"""
    municipios, total = await service.obtener_municipios(
        departamento_id=departamento_id, search=search, skip=skip, limit=limit
    )
    return {
        "data": [MunicipioListResponse.model_validate(m) for m in municipios],
        "total": total,
    }


@router.get("/municipios/{municipio_id}", response_model=MunicipioResponse)
async def obtener_municipio(
    municipio_id: UUID,
    service: GeografiaService = Depends(get_service),
):
    """Obtiene un municipio con su departamento"""
    municipio = await service.obtener_municipio_por_id(municipio_id)
    if municipio is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Municipio no encontrado",
        )
    return municipio


@router.post("/municipios", response_model=MunicipioResponse, status_code=status.HTTP_201_CREATED)
async def crear_municipio(
    data: MunicipioCreate,
    service: GeografiaService = Depends(get_service),
):
    """Crea un nuevo municipio"""
    try:
        municipio = await service.crear_municipio(data.model_dump())
        return municipio
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/municipios/{municipio_id}", response_model=MunicipioResponse)
async def actualizar_municipio(
    municipio_id: UUID,
    data: MunicipioUpdate,
    service: GeografiaService = Depends(get_service),
):
    """Actualiza un municipio"""
    try:
        municipio = await service.actualizar_municipio(
            municipio_id, data.model_dump(exclude_unset=True)
        )
        if municipio is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Municipio no encontrado",
            )
        return municipio
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/municipios/{municipio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_municipio(
    municipio_id: UUID,
    service: GeografiaService = Depends(get_service),
):
    """Elimina un municipio"""
    eliminado = await service.eliminar_municipio(municipio_id)
    if not eliminado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Municipio no encontrado",
        )


# ============================================================
# IMPORT/EXPORT
# ============================================================

@router.get("/exportar/excel")
async def exportar_excel(
    service: GeografiaService = Depends(get_service),
):
    """Exporta geografía a Excel (2 hojas: Departamentos y Municipios)"""
    archivo = await service.exportar_excel()

    return StreamingResponse(
        archivo,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=geografia_guatemala.xlsx"},
    )


@router.post("/importar/excel", response_model=GeografiaImportResult)
async def importar_excel(
    archivo: UploadFile,
    sobrescribir: bool = Query(False, description="Si es True, actualiza registros existentes"),
    service: GeografiaService = Depends(get_service),
):
    """
    Importa geografía desde Excel (2 hojas: Departamentos y Municipios).
    
    Hoja 'Departamentos': codigo_iso, nombre
    Hoja 'Municipios': codigo_iso, nombre, departamento_codigo
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