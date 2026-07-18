from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.dependencies import resolve_public_id
from app.core.security import DataScope, get_data_scope
from app.db.session import get_tenant_db
from app.models.tenant_models import InventarioItem, InventarioToma
from app.schemas.inventario.item import ItemCreate, ItemResponse, ItemUpdate
from app.services.inventario import ItemService

from .helpers import item_a_response

router = APIRouter()


async def _cargar_item(
    db: AsyncSession, public_id: UUID, tenant_id: int
) -> InventarioItem:
    """Carga un item con sus relaciones validando tenant."""
    stmt = (
        select(InventarioItem)
        .join(InventarioToma)
        .options(
            joinedload(InventarioItem.toma),
            joinedload(InventarioItem.producto),
            joinedload(InventarioItem.bodega),
        )
        .where(
            and_(
                InventarioItem.public_id == public_id,
                InventarioToma.tenant_id == tenant_id,
            )
        )
    )
    result = await db.execute(stmt)
    item = result.unique().scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item no encontrado",
        )
    return item


@router.post(
    "/tomas/{toma_public_id}",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar item a toma",
)
async def crear_item(
    toma_public_id: UUID,
    data: ItemCreate,
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    toma = await resolve_public_id(
        db, InventarioToma, toma_public_id, scope.tenant_id,
        "Toma de inventario no encontrada",
    )

    svc = ItemService(db)
    try:
        item = await svc.agregar(toma, data, scope.user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )

    # Recargar relaciones para la respuesta
    return await _cargar_item(db, item.public_id, scope.tenant_id)


@router.get(
    "/tomas/{toma_public_id}",
    response_model=list[ItemResponse],
    summary="Listar items de una toma",
)
async def listar_items(
    toma_public_id: UUID,
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    toma = await resolve_public_id(
        db, InventarioToma, toma_public_id, scope.tenant_id,
        "Toma de inventario no encontrada",
    )

    stmt = (
        select(InventarioItem)
        .options(
            joinedload(InventarioItem.toma),
            joinedload(InventarioItem.producto),
            joinedload(InventarioItem.bodega),
        )
        .where(InventarioItem.toma_id == toma.id)
        .order_by(InventarioItem.bodega_codigo, InventarioItem.codigo)
    )
    result = await db.execute(stmt)
    items = result.unique().scalars().all()
    return [item_a_response(i) for i in items]


@router.get(
    "/{public_id}",
    response_model=ItemResponse,
    summary="Obtener item por ID",
)
async def obtener_item(
    public_id: UUID,
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    item = await _cargar_item(db, public_id, scope.tenant_id)
    return item_a_response(item)


@router.put(
    "/{public_id}",
    response_model=ItemResponse,
    summary="Actualizar item",
)
async def actualizar_item(
    public_id: UUID,
    data: ItemUpdate,
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    item = await _cargar_item(db, public_id, scope.tenant_id)

    svc = ItemService(db)
    try:
        await svc.actualizar(item, data, scope.user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )

    return await _cargar_item(db, public_id, scope.tenant_id)


@router.delete(
    "/{public_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar item",
)
async def eliminar_item(
    public_id: UUID,
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    item = await _cargar_item(db, public_id, scope.tenant_id)

    svc = ItemService(db)
    try:
        await svc.eliminar(item)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )