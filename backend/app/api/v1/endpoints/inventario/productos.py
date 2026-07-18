from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import resolve_public_id
from app.core.security import DataScope, get_data_scope
from app.db.session import get_tenant_db
from app.models.tenant_models import Empresa, InventarioProducto
from app.schemas.inventario.producto import (
    ProductoCreate,
    ProductoResponse,
    ProductoUpdate,
)
from app.services.inventario import ProductoService

from .helpers import producto_a_response

router = APIRouter()


@router.post(
    "/{empresa_public_id}",
    response_model=ProductoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear producto",
)
async def crear_producto(
    empresa_public_id: UUID,
    data: ProductoCreate,
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    empresa = await resolve_public_id(
        db, Empresa, empresa_public_id, scope.tenant_id, "Empresa no encontrada"
    )

    # Validar unicidad de código si se proporciona
    if data.codigo:
        svc = ProductoService(db)
        existente = await svc.obtener_por_codigo(
            scope.tenant_id, empresa.id, data.codigo
        )
        if existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un producto con código '{data.codigo}'",
            )

    svc = ProductoService(db)
    producto = await svc.crear(scope.tenant_id, empresa.id, data, scope.user.id)
    producto.empresa = empresa
    # Recargar relación cuenta_inventario si existe
    if data.cuenta_inventario_public_id:
        await db.refresh(producto, attribute_names=["cuenta_inventario"])
    return producto_a_response(producto)


@router.get(
    "/{empresa_public_id}",
    response_model=list[ProductoResponse],
    summary="Listar productos activos",
)
async def listar_productos(
    empresa_public_id: UUID,
    search: str | None = Query(None, description="Buscar por código o descripción"),
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    empresa = await resolve_public_id(
        db, Empresa, empresa_public_id, scope.tenant_id, "Empresa no encontrada"
    )
    svc = ProductoService(db)
    productos = await svc.listar(scope.tenant_id, empresa.id, search)
    for p in productos:
        p.empresa = empresa
    return [producto_a_response(p) for p in productos]


@router.get(
    "/detalle/{public_id}",
    response_model=ProductoResponse,
    summary="Obtener producto por ID",
)
async def obtener_producto(
    public_id: UUID,
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    producto = await resolve_public_id(
        db, InventarioProducto, public_id, scope.tenant_id, "Producto no encontrado"
    )
    return producto_a_response(producto)


@router.put(
    "/{public_id}",
    response_model=ProductoResponse,
    summary="Actualizar producto",
)
async def actualizar_producto(
    public_id: UUID,
    data: ProductoUpdate,
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    producto = await resolve_public_id(
        db, InventarioProducto, public_id, scope.tenant_id, "Producto no encontrado"
    )

    # Validar unicidad de código si cambia
    if data.codigo and data.codigo != producto.codigo:
        svc = ProductoService(db)
        existente = await svc.obtener_por_codigo(
            scope.tenant_id, producto.empresa_id, data.codigo
        )
        if existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un producto con código '{data.codigo}'",
            )

    svc = ProductoService(db)
    producto_actualizado = await svc.actualizar(producto, data, scope.user.id)
    if data.cuenta_inventario_public_id is not None:
        await db.refresh(producto_actualizado, attribute_names=["cuenta_inventario"])
    return producto_a_response(producto_actualizado)


@router.delete(
    "/{public_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar producto (soft delete)",
)
async def eliminar_producto(
    public_id: UUID,
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    producto = await resolve_public_id(
        db, InventarioProducto, public_id, scope.tenant_id, "Producto no encontrado"
    )
    svc = ProductoService(db)
    await svc.eliminar(producto, scope.user.id)