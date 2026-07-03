"""Endpoint para Tipos de Persona"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.catalogos.tipo_persona import (
    TipoPersonaCreate,
    TipoPersonaResponse,
    TipoPersonaUpdate,
)
from app.services.catalogos.tipo_persona_service import TipoPersonaService

router = APIRouter(prefix="/tipos-persona", tags=["Catálogos - Tipos de Persona"])

def get_service(db: AsyncSession = Depends(get_db)) -> TipoPersonaService:
    return TipoPersonaService(db)


@router.get("/", response_model=dict)
async def listar_tipos_persona(service: TipoPersonaService = Depends(get_service)):
    """Lista tipos de persona con estructura paginada"""
    print("🔥 ENDPOINT EJECUTÁNDOSE")
    
    tipos = await service.obtener_todos()
    print(f" Service retornó {len(tipos)} objetos")
    
    # Forzar serialización explícita
    data = []
    for t in tipos:
        try:
            validated = TipoPersonaResponse.model_validate(t)
            dumped = validated.model_dump(exclude_none=False)
            print(f"🔥 Objeto serializado: {dumped}")
            data.append(dumped)
        except Exception as e:
            print(f"🔥 ERROR serializando: {e}")
    
    return {
        "data": data,
        "total": len(data),
        "skip": 0,
        "limit": 50
    }


@router.get("/{tipo_id}", response_model=TipoPersonaResponse)
async def obtener_tipo_persona(
    tipo_id: UUID, service: TipoPersonaService = Depends(get_service)
):
    tipo = await service.obtener_por_id(tipo_id)
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de persona no encontrado")
    return tipo


@router.post("/", response_model=TipoPersonaResponse, status_code=201)
async def crear_tipo_persona(
    data: TipoPersonaCreate, service: TipoPersonaService = Depends(get_service)
):
    try:
        return await service.crear(data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{tipo_id}", response_model=TipoPersonaResponse)
async def actualizar_tipo_persona(
    tipo_id: UUID,
    data: TipoPersonaUpdate,
    service: TipoPersonaService = Depends(get_service),
):
    tipo = await service.actualizar(tipo_id, data.model_dump(exclude_unset=True))
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de persona no encontrado")
    return tipo


@router.delete("/{tipo_id}", status_code=204)
async def eliminar_tipo_persona(
    tipo_id: UUID, service: TipoPersonaService = Depends(get_service)
):
    if not await service.eliminar(tipo_id):
        raise HTTPException(status_code=404, detail="Tipo de persona no encontrado")