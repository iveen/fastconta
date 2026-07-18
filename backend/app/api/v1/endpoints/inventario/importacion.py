from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.dependencies import resolve_public_id
from app.core.security import DataScope, get_data_scope
from app.db.session import get_tenant_db
from app.models.tenant_models import InventarioImportacion, InventarioToma
from app.schemas.inventario.importacion import ImportacionResponse
from app.services.inventario import ImportService

from .helpers import importacion_a_response

router = APIRouter()


@router.post(
    "/tomas/{toma_public_id}/importar",
    response_model=ImportacionResponse,
    summary="Importar inventario desde archivo",
)
async def importar_inventario(
    toma_public_id: UUID,
    file: UploadFile = File(...),
    modo: str = Query(
        "REEMPLAZAR",
        pattern="^(REEMPLAZAR|AGREGAR)$",
        description="REEMPLAZAR: borra items actuales; AGREGAR: conserva existentes",
    ),
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    toma = await resolve_public_id(
        db, InventarioToma, toma_public_id, scope.tenant_id,
        "Toma de inventario no encontrada",
    )

    filename = (file.filename or "").lower()
    if not filename.endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato no soportado. Use .xlsx, .xls o .csv",
        )

    svc = ImportService(db)
    try:
        importacion = await svc.importar(toma, file, scope.user.id, modo)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )

    # Cargar relación toma para el helper
    await db.refresh(importacion, attribute_names=["toma"])
    return importacion_a_response(importacion)


@router.get(
    "/tomas/{toma_public_id}/historial",
    response_model=list[ImportacionResponse],
    summary="Historial de importaciones de una toma",
)
async def listar_importaciones(
    toma_public_id: UUID,
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    toma = await resolve_public_id(
        db, InventarioToma, toma_public_id, scope.tenant_id,
        "Toma de inventario no encontrada",
    )

    stmt = (
        select(InventarioImportacion)
        .options(joinedload(InventarioImportacion.toma))
        .where(InventarioImportacion.toma_id == toma.id)
        .order_by(InventarioImportacion.created_at.desc())
    )
    result = await db.execute(stmt)
    importaciones = result.unique().scalars().all()
    return [importacion_a_response(i) for i in importaciones]