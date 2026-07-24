"""Endpoint para Catálogo de Impuestos"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.sat.impuesto import (
    ImpuestoCreate,
    ImpuestoListResponse,
    ImpuestoResponse,
    ImpuestoUpdate,
)
from app.services.sat.impuesto_service import ImpuestoService

router = APIRouter(prefix="/impuestos", tags=["Catálogos - Impuestos"])


def get_service(db: AsyncSession = Depends(get_db)) -> ImpuestoService:
    return ImpuestoService(db)


@router.get("/", response_model=dict)
async def listar_impuestos(
    activo: bool | None = Query(None),
    search: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: ImpuestoService = Depends(get_service),
):
    """Lista impuestos con paginación"""
    impuestos, total = await service.obtener_todos(
        activo=activo, search=search, skip=skip, limit=limit
    )
    return {
        "data": [ImpuestoListResponse.model_validate(i).model_dump() for i in impuestos],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/activos", response_model=list[ImpuestoListResponse])
async def listar_impuestos_activos(
    service: ImpuestoService = Depends(get_service),
):
    """Lista todos los impuestos activos (para dropdowns)"""
    return await service.obtener_todos_activos()


@router.get("/{impuesto_id}", response_model=ImpuestoResponse)
async def obtener_impuesto(
    impuesto_id: int,  # ✅ BIGINT
    service: ImpuestoService = Depends(get_service),
):
    """Obtiene un impuesto por ID"""
    impuesto = await service.obtener_por_id(impuesto_id)
    if not impuesto:
        raise HTTPException(status_code=404, detail="Impuesto no encontrado")
    return impuesto


@router.post("/", response_model=ImpuestoResponse, status_code=201)
async def crear_impuesto(
    data: ImpuestoCreate,
    service: ImpuestoService = Depends(get_service),
):
    """Crea un nuevo impuesto"""
    try:
        return await service.crear(data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{impuesto_id}", response_model=ImpuestoResponse)
async def actualizar_impuesto(
    impuesto_id: int,  # ✅ BIGINT
    data: ImpuestoUpdate,
    service: ImpuestoService = Depends(get_service),
):
    """Actualiza un impuesto"""
    impuesto = await service.actualizar(impuesto_id, data.model_dump(exclude_unset=True))
    if not impuesto:
        raise HTTPException(status_code=404, detail="Impuesto no encontrado")
    return impuesto


@router.delete("/{impuesto_id}", status_code=204)
async def eliminar_impuesto(
    impuesto_id: int,  # ✅ BIGINT
    service: ImpuestoService = Depends(get_service),
):
    """Elimina un impuesto (soft delete)"""
    if not await service.eliminar(impuesto_id):
        raise HTTPException(status_code=404, detail="Impuesto no encontrado")