from uuid import UUID

from fastapi import Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import DataScope, get_data_scope
from app.core.tenant_utils import set_tenant_search_path
from app.db.session import get_tenant_db
from app.models.tenant_models import Empresa


# ==============================================================================
# DEPENDENCIA DE SEGURIDAD (ASYNC)
# ==============================================================================
async def verificar_acceso_empresa(
    empresa_id: UUID = Query(..., description="ID de la empresa a verificar"),
    tenant_id: str | None = Query(None, description="ID del tenant (para superadmin)"),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_tenant_db)
) -> UUID:
    """
    Dependencia asíncrona que valida el acceso a la empresa.
    Configura el schema del tenant y verifica que la empresa exista.
    """
    # Configurar schema del tenant
    await set_tenant_search_path(db, scope, tenant_id)
    
    # Validar que la empresa exista en el tenant
    stmt = select(Empresa).where(Empresa.id == empresa_id)
    result = await db.execute(stmt)
    empresa = result.scalar_one_or_none()
    
    if not empresa:
        raise HTTPException(
            status_code=404, 
            detail="Empresa no encontrada o acceso no autorizado"
        )
    
    return empresa_id
