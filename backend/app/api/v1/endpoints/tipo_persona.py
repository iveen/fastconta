"""Endpoint para gestión de Tipos de Persona"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.configuracion_fiscal.tipo_persona import (
    TipoPersonaCreate,
    TipoPersonaListResponse,
    TipoPersonaResponse,
    TipoPersonaUpdate,
)
from app.services.configuracion_fiscal.tipo_persona_service import TipoPersonaService

router = APIRouter(
    prefix="/tipos-persona",
    tags=["Configuración Fiscal - Tipos de Persona"],
)


def get_service(db: AsyncSession = Depends(get_db)) -> TipoPersonaService:
    return TipoPersonaService(db)


# ============================================================
# LISTAR
# ============================================================
@router.get("/", response_model=dict)
async def listar_tipos_persona(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: TipoPersonaService = Depends(get_service),
):
    """Lista tipos de persona con paginación"""
    tipos, total = await service.obtener_todos(skip=skip, limit=limit)
    return {
        "data": [TipoPersonaListResponse.model_validate(t) for t in tipos],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


# ============================================================
# LISTAR TODOS (para dropdowns)
# ============================================================
@router.get("/lista", response_model=list[TipoPersonaListResponse])
async def listar_todos_tipos_persona(
    service: TipoPersonaService = Depends(get_service),
):
    """Lista todos los tipos de persona (sin paginación, para dropdowns)"""
    return await service.obtener_todos_lista()


# ============================================================
# OBTENER POR ID
# ============================================================
@router.get("/{tipo_id}", response_model=TipoPersonaResponse)
async def obtener_tipo_persona(
    tipo_id: UUID,
    service: TipoPersonaService = Depends(get_service),
):
    """Obtiene un tipo de persona por ID"""
    tipo = await service.obtener_por_id(tipo_id)
    if tipo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de persona no encontrado",
        )
    return tipo


# ============================================================
# CREAR
# ============================================================
@router.post("/", response_model=TipoPersonaResponse, status_code=status.HTTP_201_CREATED)
async def crear_tipo_persona(
    data: TipoPersonaCreate,
    service: TipoPersonaService = Depends(get_service),
):
    """Crea un nuevo tipo de persona"""
    try:
        tipo = await service.crear(data.model_dump())
        return tipo
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================
# ACTUALIZAR
# ============================================================
@router.patch("/{tipo_id}", response_model=TipoPersonaResponse)
async def actualizar_tipo_persona(
    tipo_id: UUID,
    data: TipoPersonaUpdate,
    service: TipoPersonaService = Depends(get_service),
):
    """Actualiza un tipo de persona"""
    try:
        tipo = await service.actualizar(tipo_id, data.model_dump(exclude_unset=True))
        if tipo is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tipo de persona no encontrado",
            )
        return tipo
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================
# ELIMINAR
# ============================================================
@router.delete("/{tipo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_tipo_persona(
    tipo_id: UUID,
    service: TipoPersonaService = Depends(get_service),
):
    """Elimina un tipo de persona"""
    eliminado = await service.eliminar(tipo_id)
    if not eliminado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de persona no encontrado",
        )