from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import DataScope, get_data_scope
from app.db.session import get_tenant_db
from app.models.tenant_models import InventarioToma
from app.services.inventario import ExportService

router = APIRouter()


@router.get(
    "/tomas/{toma_public_id}",
    summary="Exportar toma de inventario a Excel o PDF",
)
async def exportar_toma(
    toma_public_id: UUID,
    formato: str = Query(
        "excel",
        pattern="^(excel|pdf)$",
        description="Formato de exportación: 'excel' (.xlsx) o 'pdf'",
    ),
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    # Validar que la toma existe y pertenece al tenant
    from sqlalchemy import and_, select
    stmt = select(InventarioToma).where(
        and_(
            InventarioToma.public_id == toma_public_id,
            InventarioToma.tenant_id == scope.tenant_id,
        )
    )
    result = await db.execute(stmt)
    toma = result.scalar_one_or_none()
    if not toma:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Toma de inventario no encontrada",
        )

    svc = ExportService(db)
    try:
        contenido, nombre_archivo = await svc.exportar_toma(
            toma.id, scope.tenant_id, formato=formato
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando archivo: {str(e)}",
        )

    media_type = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if formato == "excel"
        else "application/pdf"
    )

    return Response(
        content=contenido,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{nombre_archivo}"'
        },
    )