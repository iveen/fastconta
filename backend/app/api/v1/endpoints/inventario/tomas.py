from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.dependencies import resolve_public_id
from app.core.security import DataScope, get_data_scope
from app.db.session import get_tenant_db
from app.models.tenant_models import Empresa, InventarioItem, InventarioToma
from app.schemas.inventario.toma import (
    TomaCreate,
    TomaListResponse,
    TomaResponse,
    TomaUpdate,
)
from app.services.inventario import TomaService

from .helpers import toma_a_list_response, toma_a_response

router = APIRouter()


async def _cargar_toma_completa(
    db: AsyncSession, public_id: UUID, tenant_id: int
) -> InventarioToma:
    """Carga una toma con todas sus relaciones para respuesta completa."""
    stmt = (
        select(InventarioToma)
        .options(
            selectinload(InventarioToma.items)
                .joinedload(InventarioItem.bodega),
            selectinload(InventarioToma.items)
                .joinedload(InventarioItem.producto),
            joinedload(InventarioToma.empresa),
            joinedload(InventarioToma.partida_ajuste),
        )
        .where(
            and_(
                InventarioToma.public_id == public_id,
                InventarioToma.tenant_id == tenant_id,
            )
        )
    )
    result = await db.execute(stmt)
    toma = result.unique().scalar_one_or_none()
    if not toma:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Toma de inventario no encontrada",
        )
    return toma


async def _cargar_toma_simple(
    db: AsyncSession, public_id: UUID, tenant_id: int
) -> InventarioToma:
    """Carga una toma con empresa (para listado)."""
    stmt = (
        select(InventarioToma)
        .options(joinedload(InventarioToma.empresa))
        .where(
            and_(
                InventarioToma.public_id == public_id,
                InventarioToma.tenant_id == tenant_id,
            )
        )
    )
    result = await db.execute(stmt)
    toma = result.unique().scalar_one_or_none()
    if not toma:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Toma de inventario no encontrada",
        )
    return toma


@router.post(
    "",
    response_model=TomaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear toma de inventario",
)
async def crear_toma(
    data: TomaCreate,
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    empresa = await resolve_public_id(
        db, Empresa, data.empresa_public_id, scope.tenant_id, "Empresa no encontrada"
    )

    # Construir schema interno con empresa_id
    data_dict = data.model_dump()
    data_dict["empresa_id"] = empresa.id
    del data_dict["empresa_public_id"]
    data_interna = TomaCreate(**data_dict)

    svc = TomaService(db)
    try:
        toma = await svc.crear(scope.tenant_id, data_interna, scope.user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )

    return await _cargar_toma_completa(db, toma.public_id, scope.tenant_id)


@router.get(
    "",
    response_model=list[TomaListResponse],
    summary="Listar tomas de inventario",
)
async def listar_tomas(
    empresa_public_id: UUID | None = Query(None),
    estado: str | None = Query(None),
    tipo: str | None = Query(None),
    anio: int | None = Query(None),
    mes: int | None = Query(None),
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    empresa_id = None
    if empresa_public_id:
        empresa = await resolve_public_id(
            db, Empresa, empresa_public_id, scope.tenant_id, "Empresa no encontrada"
        )
        empresa_id = empresa.id

    svc = TomaService(db)
    tomas = await svc.listar(
        scope.tenant_id,
        empresa_id=empresa_id,
        estado=estado,
        tipo=tipo,
        anio=anio,
        mes=mes,
    )

    # Cargar empresa para cada toma
    stmt = (
        select(InventarioToma)
        .options(joinedload(InventarioToma.empresa))
        .where(InventarioToma.id.in_([t.id for t in tomas]))
    )
    result = await db.execute(stmt)
    tomas_con_empresa = {t.id: t for t in result.unique().scalars().all()}

    return [
        toma_a_list_response(tomas_con_empresa[t.id])
        for t in tomas
        if t.id in tomas_con_empresa
    ]


@router.get(
    "/{public_id}",
    response_model=TomaResponse,
    summary="Obtener toma de inventario con items",
)
async def obtener_toma(
    public_id: UUID,
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    toma = await _cargar_toma_completa(db, public_id, scope.tenant_id)
    return toma_a_response(toma)


@router.put(
    "/{public_id}",
    response_model=TomaResponse,
    summary="Actualizar toma de inventario",
)
async def actualizar_toma(
    public_id: UUID,
    data: TomaUpdate,
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    toma = await _cargar_toma_completa(db, public_id, scope.tenant_id)

    svc = TomaService(db)
    try:
        await svc.actualizar(toma, data, scope.user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )

    return await _cargar_toma_completa(db, public_id, scope.tenant_id)


@router.post(
    "/{public_id}/confirmar",
    response_model=TomaResponse,
    summary="Confirmar toma de inventario",
)
async def confirmar_toma(
    public_id: UUID,
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    toma = await _cargar_toma_completa(db, public_id, scope.tenant_id)

    svc = TomaService(db)
    try:
        await svc.confirmar(toma, scope.user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )

    return await _cargar_toma_completa(db, public_id, scope.tenant_id)


@router.delete(
    "/{public_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar toma de inventario",
)
async def eliminar_toma(
    public_id: UUID,
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    toma = await _cargar_toma_simple(db, public_id, scope.tenant_id)

    svc = TomaService(db)
    try:
        await svc.eliminar(toma)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )