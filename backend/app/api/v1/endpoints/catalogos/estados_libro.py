"""Endpoint para Estados de Libro SAT"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.catalogos.estado_libro import (
    EstadoLibroCreate,
    EstadoLibroListResponse,
    EstadoLibroResponse,
    EstadoLibroUpdate,
)
from app.services.catalogos.estado_libro_service import EstadoLibroService

router = APIRouter(
    prefix="/estados-libro",
    tags=["Catálogos - Estados de Libro SAT"],
)


def get_service(db: AsyncSession = Depends(get_db)) -> EstadoLibroService:
    return EstadoLibroService(db)


@router.get("/", response_model=dict)
async def listar_estados_libro(
    is_active: bool | None = Query(None),
    search: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: EstadoLibroService = Depends(get_service),
):
    """Lista estados de libro con paginación"""
    estados, total = await service.obtener_todos(
        is_active=is_active, search=search, skip=skip, limit=limit
    )
    return {
        "data": [EstadoLibroListResponse.model_validate(e).model_dump() for e in estados],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/activos", response_model=list[EstadoLibroListResponse])
async def listar_estados_libro_activos(
    service: EstadoLibroService = Depends(get_service),
):
    """Lista todos los estados de libro activos (para dropdowns)"""
    return await service.obtener_todos_activos()


@router.get("/{estado_id}", response_model=EstadoLibroResponse)
async def obtener_estado_libro(
    estado_id: int,  # ✅ BIGINT
    service: EstadoLibroService = Depends(get_service),
):
    """Obtiene un estado de libro por ID"""
    estado = await service.obtener_por_id(estado_id)
    if not estado:
        raise HTTPException(status_code=404, detail="Estado de libro no encontrado")
    return estado


@router.post("/", response_model=EstadoLibroResponse, status_code=201)
async def crear_estado_libro(
    data: EstadoLibroCreate,
    service: EstadoLibroService = Depends(get_service),
):
    """Crea un nuevo estado de libro"""
    try:
        return await service.crear(data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{estado_id}", response_model=EstadoLibroResponse)
async def actualizar_estado_libro(
    estado_id: int,  # ✅ BIGINT
    data: EstadoLibroUpdate,
    service: EstadoLibroService = Depends(get_service),
):
    """Actualiza un estado de libro"""
    estado = await service.actualizar(estado_id, data.model_dump(exclude_unset=True))
    if not estado:
        raise HTTPException(status_code=404, detail="Estado de libro no encontrado")
    return estado


@router.delete("/{estado_id}", status_code=204)
async def eliminar_estado_libro(
    estado_id: int,  # ✅ BIGINT
    service: EstadoLibroService = Depends(get_service),
):
    """Elimina un estado de libro (soft delete)"""
    if not await service.eliminar(estado_id):
        raise HTTPException(status_code=404, detail="Estado de libro no encontrado")