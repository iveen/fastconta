"""Endpoint para Categorías de Activos Fijos"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.catalogos.categoria_activo import (
    CategoriaActivoFijoCreate,
    CategoriaActivoFijoListResponse,
    CategoriaActivoFijoResponse,
    CategoriaActivoFijoUpdate,
)
from app.services.catalogos.categoria_activo_service import CategoriaActivoService

router = APIRouter(prefix="/categorias-activos", tags=["Catálogos - Categorías de Activos"])


def get_service(db: AsyncSession = Depends(get_db)) -> CategoriaActivoService:
    return CategoriaActivoService(db)


@router.get("/", response_model=dict)
async def listar_categorias(
    is_active: bool | None = Query(None),
    search: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: CategoriaActivoService = Depends(get_service),
):
    categorias, total = await service.obtener_todos(
        is_active=is_active, search=search, skip=skip, limit=limit
    )
    return {
        "data": [CategoriaActivoFijoListResponse.model_validate(c) for c in categorias],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/activos", response_model=list[CategoriaActivoFijoListResponse])
async def listar_categorias_activos(service: CategoriaActivoService = Depends(get_service)):
    return await service.obtener_todos_activos()


@router.get("/{categoria_id}", response_model=CategoriaActivoFijoResponse)
async def obtener_categoria(
    categoria_id: UUID, service: CategoriaActivoService = Depends(get_service)
):
    categoria = await service.obtener_por_id(categoria_id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return categoria


@router.post("/", response_model=CategoriaActivoFijoResponse, status_code=201)
async def crear_categoria(
    data: CategoriaActivoFijoCreate, service: CategoriaActivoService = Depends(get_service)
):
    try:
        return await service.crear(data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{categoria_id}", response_model=CategoriaActivoFijoResponse)
async def actualizar_categoria(
    categoria_id: UUID,
    data: CategoriaActivoFijoUpdate,
    service: CategoriaActivoService = Depends(get_service),
):
    categoria = await service.actualizar(categoria_id, data.model_dump(exclude_unset=True))
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return categoria


@router.delete("/{categoria_id}", status_code=204)
async def eliminar_categoria(
    categoria_id: UUID, service: CategoriaActivoService = Depends(get_service)
):
    if not await service.eliminar(categoria_id):
        raise HTTPException(status_code=404, detail="Categoría no encontrada")