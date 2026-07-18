from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.security import DataScope, get_data_scope
from app.db.session import get_tenant_db
from app.models.tenant_models import InventarioToma
from app.schemas.inventario.costo_ventas import CostoVentasResponse
from app.services.inventario import CostoVentasService

from .helpers import costo_ventas_a_response

router = APIRouter()


@router.get(
    "/tomas/{toma_public_id}",
    response_model=CostoVentasResponse,
    summary="Calcular costo de ventas",
    description=(
        "CV = Inventario Inicial + Compras del Período - Inventario Final. "
        "El inventario inicial proviene de la toma anterior CONFIRMADA/CONTABILIZADA."
    ),
)
async def calcular_costo_ventas(
    toma_public_id: UUID,
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    # Cargar toma
    stmt = (
        select(InventarioToma)
        .options(joinedload(InventarioToma.empresa))
        .where(
            and_(
                InventarioToma.public_id == toma_public_id,
                InventarioToma.tenant_id == scope.tenant_id,
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

    svc = CostoVentasService(db)
    try:
        resultado = await svc.calcular(toma.id, scope.tenant_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )

    # Enriquecer con public_ids para la respuesta
    resultado["toma_public_id"] = str(toma.public_id)
    resultado["empresa_public_id"] = (
        str(toma.empresa.public_id) if toma.empresa else str(toma.empresa_id)
    )
    return costo_ventas_a_response(resultado)