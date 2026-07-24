"""Endpoint para Tipos de Persona"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.catalogos.tipo_persona import (
    TipoPersonaCreate,
    TipoPersonaResponse,
    TipoPersonaUpdate,
)
from app.services.deprecated.tipo_persona_service import TipoPersonaService

router = APIRouter(prefix="/tipos-persona", tags=["Catálogos - Tipos de Persona"])


def get_service(db: AsyncSession = Depends(get_db)) -> TipoPersonaService: #noqa B008
    return TipoPersonaService(db)


@router.get("/", response_model=dict)
async def listar_tipos_persona(
    search: str | None = Query(None, description="Buscar por nombre"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: TipoPersonaService = Depends(get_service), #noqa B008
):
    """Lista tipos de persona con estructura paginada"""
    tipos, total = await service.obtener_todos(search=search, skip=skip, limit=limit)
    
    return {
        "data": [TipoPersonaResponse.model_validate(t).model_dump() for t in tipos],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/lista", response_model=list[TipoPersonaResponse])
async def listar_tipos_persona_activos(
    service: TipoPersonaService = Depends(get_service), #noqa B008
):
    """Lista todos los tipos de persona activos (para dropdowns)"""
    return await service.obtener_todos_activos() 


@router.get("/{tipo_id}", response_model=TipoPersonaResponse)
async def obtener_tipo_persona(
    tipo_id: int,  # ✅ BIGINT (era UUID)
    service: TipoPersonaService = Depends(get_service), #noqa B008
):
    """Obtiene un tipo de persona por ID"""
    tipo = await service.obtener_por_id(tipo_id)
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de persona no encontrado")
    return tipo


@router.post("/", response_model=TipoPersonaResponse, status_code=201)
async def crear_tipo_persona(
    data: TipoPersonaCreate,
    service: TipoPersonaService = Depends(get_service), #noqa B008
):
    """Crea un nuevo tipo de persona"""
    try:
        return await service.crear(data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{tipo_id}", response_model=TipoPersonaResponse)
async def actualizar_tipo_persona(
    tipo_id: int,  # ✅ BIGINT (era UUID)
    data: TipoPersonaUpdate,
    service: TipoPersonaService = Depends(get_service), #noqa B008
):
    """Actualiza un tipo de persona"""
    tipo = await service.actualizar(tipo_id, data.model_dump(exclude_unset=True))
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de persona no encontrado")
    return tipo


@router.delete("/{tipo_id}", status_code=204)
async def eliminar_tipo_persona(
    tipo_id: int,  # ✅ BIGINT (era UUID)
    service: TipoPersonaService = Depends(get_service), #noqa B008
):
    """Elimina un tipo de persona (soft delete)"""
    if not await service.eliminar(tipo_id):
        raise HTTPException(status_code=404, detail="Tipo de persona no encontrado")