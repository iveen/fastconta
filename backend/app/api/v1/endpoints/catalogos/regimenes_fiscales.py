"""Endpoint para gestión de Regímenes Fiscales"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.sat.regimen_fiscal import (
    RegimenFiscalCreate,
    RegimenFiscalDetailResponse,
    RegimenFiscalListResponse,
    RegimenFiscalResponse,
    RegimenFiscalUpdate,
)
from app.services.sat.regimen_fiscal_service import (
    RegimenFiscalService,
)

router = APIRouter(
    prefix="/regimenes-fiscales",
    tags=["Configuración Fiscal - Regímenes Fiscales"],
)


def get_service(db: AsyncSession = Depends(get_db)) -> RegimenFiscalService:
    return RegimenFiscalService(db)


# ============================================================
# LISTAR
# ============================================================
@router.get("/", response_model=dict)
async def listar_regimenes(
    is_active: bool | None = Query(None, description="Filtrar por estado activo"),
    search: str | None = Query(None, description="Buscar por código, nombre o descripción"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: RegimenFiscalService = Depends(get_service),
):
    """Lista regímenes fiscales con filtros y paginación"""
    regimenes, total = await service.obtener_todos(
        is_active=is_active, search=search, skip=skip, limit=limit
    )
    return {
        "data": [RegimenFiscalListResponse.model_validate(r).model_dump() for r in regimenes],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


# ============================================================
# LISTAR ACTIVOS (para dropdowns)
# ============================================================
@router.get("/activos", response_model=list[RegimenFiscalListResponse])
async def listar_regimenes_activos(
    service: RegimenFiscalService = Depends(get_service),
):
    """Lista todos los regímenes fiscales activos (sin paginación, para dropdowns)"""
    return await service.obtener_todos_lista()


# ============================================================
# OBTENER POR ID (con formularios asociados)
# ============================================================
@router.get("/{regimen_id}", response_model=RegimenFiscalDetailResponse)
async def obtener_regimen(
    regimen_id: int,  # ✅ BIGINT (era UUID)
    service: RegimenFiscalService = Depends(get_service),
):
    """Obtiene un régimen fiscal por ID, incluyendo formularios SAT asociados"""
    regimen = await service.obtener_por_id(regimen_id)
    if regimen is None:
        raise HTTPException(
            status_code=404,
            detail="Régimen fiscal no encontrado",
        )
    
    # Construir respuesta con formularios asociados
    formularios = await service.obtener_formularios_asociados(regimen_id)
    response_data = RegimenFiscalResponse.model_validate(regimen).model_dump()
    response_data["formularios_asociados"] = formularios
    return RegimenFiscalDetailResponse(**response_data)


# ============================================================
# CREAR
# ============================================================
@router.post("/", response_model=RegimenFiscalResponse, status_code=201)
async def crear_regimen(
    data: RegimenFiscalCreate,
    service: RegimenFiscalService = Depends(get_service),
):
    """Crea un nuevo régimen fiscal"""
    try:
        return await service.crear(data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# ACTUALIZAR
# ============================================================
@router.patch("/{regimen_id}", response_model=RegimenFiscalResponse)
async def actualizar_regimen(
    regimen_id: int,  # ✅ BIGINT (era UUID)
    data: RegimenFiscalUpdate,
    service: RegimenFiscalService = Depends(get_service),
):
    """Actualiza un régimen fiscal"""
    regimen = await service.actualizar(regimen_id, data.model_dump(exclude_unset=True))
    if regimen is None:
        raise HTTPException(
            status_code=404,
            detail="Régimen fiscal no encontrado",
        )
    return regimen


# ============================================================
# ELIMINAR (soft delete)
# ============================================================
@router.delete("/{regimen_id}", status_code=204)
async def eliminar_regimen(
    regimen_id: int,  # ✅ BIGINT (era UUID)
    service: RegimenFiscalService = Depends(get_service),
):
    """Desactiva un régimen fiscal (soft delete)"""
    eliminado = await service.eliminar(regimen_id)
    if not eliminado:
        raise HTTPException(
            status_code=404,
            detail="Régimen fiscal no encontrado",
        )