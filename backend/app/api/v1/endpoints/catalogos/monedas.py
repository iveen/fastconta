"""Endpoint para Catálogo de Monedas"""
from uuid import UUID

from app.db.session import get_db
from app.schemas.catalogos.moneda import (
    MonedaCreate,
    MonedaListResponse,
    MonedaResponse,
    MonedaUpdate,
)
from app.services.catalogos.moneda_service import MonedaService
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/monedas", tags=["Catálogos - Monedas"])


def get_service(db: AsyncSession = Depends(get_db)) -> MonedaService:
    return MonedaService(db)


@router.get("/", response_model=dict)
async def listar_monedas(
    activo: bool | None = Query(None),
    search: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: MonedaService = Depends(get_service),
):
    monedas, total = await service.obtener_todos(
        activo=activo, search=search, skip=skip, limit=limit
    )
    return {
        "data": [MonedaListResponse.model_validate(m) for m in monedas],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/activos", response_model=list[MonedaListResponse])
async def listar_monedas_activos(service: MonedaService = Depends(get_service)):
    return await service.obtener_todos_activos()


@router.get("/{moneda_id}", response_model=MonedaResponse)
async def obtener_moneda(moneda_id: UUID, service: MonedaService = Depends(get_service)):
    moneda = await service.obtener_por_id(moneda_id)
    if not moneda:
        raise HTTPException(status_code=404, detail="Moneda no encontrada")
    return moneda


@router.post("/", response_model=MonedaResponse, status_code=201)
async def crear_moneda(data: MonedaCreate, service: MonedaService = Depends(get_service)):
    try:
        return await service.crear(data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{moneda_id}", response_model=MonedaResponse)
async def actualizar_moneda(
    moneda_id: UUID, data: MonedaUpdate, service: MonedaService = Depends(get_service)
):
    moneda = await service.actualizar(moneda_id, data.model_dump(exclude_unset=True))
    if not moneda:
        raise HTTPException(status_code=404, detail="Moneda no encontrada")
    return moneda


@router.delete("/{moneda_id}", status_code=204)
async def eliminar_moneda(moneda_id: UUID, service: MonedaService = Depends(get_service)):
    if not await service.eliminar(moneda_id):
        raise HTTPException(status_code=404, detail="Moneda no encontrada")