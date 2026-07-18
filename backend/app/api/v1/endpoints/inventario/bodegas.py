from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import resolve_public_id
from app.core.security import DataScope, get_data_scope
from app.db.session import get_tenant_db
from app.models.tenant_models import Empresa, InventarioBodega
from app.schemas.inventario.bodega import BodegaCreate, BodegaResponse, BodegaUpdate
from app.services.inventario import BodegaService

from .helpers import bodega_a_response

router = APIRouter()


@router.post(
    "/{empresa_public_id}",
    response_model=BodegaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear bodega",
)
async def crear_bodega(
    empresa_public_id: UUID,
    data: BodegaCreate,
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    empresa = await resolve_public_id(
        db, Empresa, empresa_public_id, scope.tenant_id, "Empresa no encontrada"
    )

    svc = BodegaService(db)
    existente = await svc.obtener_por_codigo(scope.tenant_id, empresa.id, data.codigo)
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una bodega con código '{data.codigo}'",
        )

    bodega = await svc.crear(scope.tenant_id, empresa.id, data, scope.user.id)
    # Cargar empresa para el helper
    bodega.empresa = empresa
    return bodega_a_response(bodega)


@router.get(
    "/{empresa_public_id}",
    response_model=list[BodegaResponse],
    summary="Listar bodegas activas",
)
async def listar_bodegas(
    empresa_public_id: UUID,
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    empresa = await resolve_public_id(
        db, Empresa, empresa_public_id, scope.tenant_id, "Empresa no encontrada"
    )
    svc = BodegaService(db)
    bodegas = await svc.listar(scope.tenant_id, empresa.id)
    # Asignar empresa para el helper
    for b in bodegas:
        b.empresa = empresa
    return [bodega_a_response(b) for b in bodegas]


@router.get(
    "/detalle/{public_id}",
    response_model=BodegaResponse,
    summary="Obtener bodega por ID",
)
async def obtener_bodega(
    public_id: UUID,
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    bodega = await resolve_public_id(
        db, InventarioBodega, public_id, scope.tenant_id, "Bodega no encontrada"
    )
    return bodega_a_response(bodega)


@router.put(
    "/{public_id}",
    response_model=BodegaResponse,
    summary="Actualizar bodega",
)
async def actualizar_bodega(
    public_id: UUID,
    data: BodegaUpdate,
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    bodega = await resolve_public_id(
        db, InventarioBodega, public_id, scope.tenant_id, "Bodega no encontrada"
    )

    # Validar unicidad si cambia el código
    if data.codigo and data.codigo != bodega.codigo:
        svc = BodegaService(db)
        existente = await svc.obtener_por_codigo(
            scope.tenant_id, bodega.empresa_id, data.codigo
        )
        if existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe una bodega con código '{data.codigo}'",
            )

    svc = BodegaService(db)
    bodega_actualizada = await svc.actualizar(bodega, data, scope.user.id)
    return bodega_a_response(bodega_actualizada)


@router.delete(
    "/{public_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar bodega (soft delete)",
)
async def eliminar_bodega(
    public_id: UUID,
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    bodega = await resolve_public_id(
        db, InventarioBodega, public_id, scope.tenant_id, "Bodega no encontrada"
    )

    svc = BodegaService(db)
    if await svc.tiene_items_asociados(bodega.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar una bodega con items de inventario asociados",
        )

    await svc.eliminar(bodega, scope.user.id)