"""Endpoint para Actividades Económicas SAT"""
from uuid import UUID

from app.db.session import get_db
from app.schemas.catalogos.actividad_economica import (
    ActividadEconomicaCreate,
    ActividadEconomicaListResponse,
    ActividadEconomicaResponse,
    ActividadEconomicaUpdate,
)
from app.services.catalogos.actividad_economica_service import ActividadEconomicaService
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/actividades-economicas", tags=["Catálogos - Actividades Económicas"])


def get_service(db: AsyncSession = Depends(get_db)) -> ActividadEconomicaService:
    return ActividadEconomicaService(db)


@router.get("/", response_model=dict)
async def listar_actividades(
    activa: bool | None = Query(None),
    search: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: ActividadEconomicaService = Depends(get_service),
):
    actividades, total = await service.obtener_todos(
        activa=activa, search=search, skip=skip, limit=limit
    )
    return {
        "data": [ActividadEconomicaListResponse.model_validate(a) for a in actividades],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/activas", response_model=list[ActividadEconomicaListResponse])
async def listar_actividades_activas(service: ActividadEconomicaService = Depends(get_service)):
    return await service.obtener_todos_activas()


@router.get("/{actividad_id}", response_model=ActividadEconomicaResponse)
async def obtener_actividad(
    actividad_id: UUID, service: ActividadEconomicaService = Depends(get_service)
):
    actividad = await service.obtener_por_id(actividad_id)
    if not actividad:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    return actividad


@router.post("/", response_model=ActividadEconomicaResponse, status_code=201)
async def crear_actividad(
    data: ActividadEconomicaCreate, service: ActividadEconomicaService = Depends(get_service)
):
    try:
        return await service.crear(data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{actividad_id}", response_model=ActividadEconomicaResponse)
async def actualizar_actividad(
    actividad_id: UUID,
    data: ActividadEconomicaUpdate,
    service: ActividadEconomicaService = Depends(get_service),
):
    actividad = await service.actualizar(actividad_id, data.model_dump(exclude_unset=True))
    if not actividad:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    return actividad


@router.delete("/{actividad_id}", status_code=204)
async def eliminar_actividad(
    actividad_id: UUID, service: ActividadEconomicaService = Depends(get_service)
):
    if not await service.eliminar(actividad_id):
        raise HTTPException(status_code=404, detail="Actividad no encontrada")