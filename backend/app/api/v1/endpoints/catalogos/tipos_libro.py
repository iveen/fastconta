"""Endpoint para Tipos de Libro SAT"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.sat.tipo_libro import (
    TipoLibroCreate,
    TipoLibroListResponse,
    TipoLibroResponse,
    TipoLibroUpdate,
)
from app.services.sat.tipo_libro_service import TipoLibroService

router = APIRouter(
    prefix="/tipos-libro",
    tags=["Catálogos - Tipos de Libro SAT"],
)


def get_service(db: AsyncSession = Depends(get_db)) -> TipoLibroService:
    return TipoLibroService(db)


@router.get("/", response_model=dict)
async def listar_tipos_libro(
    is_active: bool | None = Query(None),
    search: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: TipoLibroService = Depends(get_service),
):
    """Lista tipos de libro con paginación"""
    tipos, total = await service.obtener_todos(
        is_active=is_active, search=search, skip=skip, limit=limit
    )
    return {
        "data": [TipoLibroListResponse.model_validate(t).model_dump() for t in tipos],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/activos", response_model=list[TipoLibroListResponse])
async def listar_tipos_libro_activos(
    service: TipoLibroService = Depends(get_service),
):
    """Lista todos los tipos de libro activos (para dropdowns)"""
    return await service.obtener_todos_activos()


@router.get("/{tipo_id}", response_model=TipoLibroResponse)
async def obtener_tipo_libro(
    tipo_id: int,  # ✅ BIGINT
    service: TipoLibroService = Depends(get_service),
):
    """Obtiene un tipo de libro por ID"""
    tipo = await service.obtener_por_id(tipo_id)
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de libro no encontrado")
    return tipo


@router.post("/", response_model=TipoLibroResponse, status_code=201)
async def crear_tipo_libro(
    data: TipoLibroCreate,
    service: TipoLibroService = Depends(get_service),
):
    """Crea un nuevo tipo de libro"""
    try:
        return await service.crear(data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{tipo_id}", response_model=TipoLibroResponse)
async def actualizar_tipo_libro(
    tipo_id: int,  # ✅ BIGINT
    data: TipoLibroUpdate,
    service: TipoLibroService = Depends(get_service),
):
    """Actualiza un tipo de libro"""
    tipo = await service.actualizar(tipo_id, data.model_dump(exclude_unset=True))
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de libro no encontrado")
    return tipo


@router.delete("/{tipo_id}", status_code=204)
async def eliminar_tipo_libro(
    tipo_id: int,  # ✅ BIGINT
    service: TipoLibroService = Depends(get_service),
):
    """Elimina un tipo de libro (soft delete)"""
    if not await service.eliminar(tipo_id):
        raise HTTPException(status_code=404, detail="Tipo de libro no encontrado")