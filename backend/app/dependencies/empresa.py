# app/dependencies/empresa.py
import logging
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import DataScope, get_data_scope
from app.db.session import get_public_db, get_tenant_db
from app.models.tenant_models import Empresa
from app.services.empresa_service import (
    configure_search_path_for_tenant,
    get_empresa_by_id,
)

logger = logging.getLogger(__name__)


async def get_active_empresa(
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
    db: AsyncSession = Depends(get_tenant_db),
) -> Empresa:
    """
    Dependencia FastAPI que valida y retorna la empresa activa.
    
    Lee el header X-Company-Id inyectado por el frontend,
    valida que la empresa exista y esté activa en el tenant del usuario.
    
    Uso en endpoints:
        @router.get("/algo")
        async def endpoint(empresa: Empresa = Depends(get_active_empresa)):
            # empresa ya está validada y lista para usar
    """

    if not x_company_id:
        return None

    # 1. Validar formato del UUID
    try:
        empresa_id = UUID(x_company_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El identificador de empresa (X-Company-Id) no es válido."
        )
    
    # 2. Buscar empresa en el tenant actual (search_path ya configurado por get_tenant_db)
    empresa = await get_empresa_by_id(db, empresa_id)
    
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada. Verifique que tenga acceso a ella."
        )
    
    # 3. Validar que esté activa
    if not empresa.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La empresa seleccionada está inactiva. Contacte al administrador."
        )
    
    return empresa


async def get_empresa_with_tenant_context(
    empresa_id: str,
    tenant_id: str | None = Query(None, description="ID del tenant (requerido para superadmin)"),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
) -> Empresa:
    """
    Dependencia para endpoints que necesitan acceso a una empresa específica,
    incluyendo soporte para superadmin que puede especificar tenant_id.
    
    Configura automáticamente el search_path correcto.
    """
    # 1. Configurar search_path según el rol
    if scope.role_code == "superadmin":
        if not tenant_id:
            raise HTTPException(
                status_code=400, 
                detail="Superadmin debe especificar un tenant_id"
            )
        try:
            await configure_search_path_for_tenant(db, UUID(tenant_id))
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    else:
        try:
            await configure_search_path_for_tenant(db, scope.tenant_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    
    # 2. Buscar empresa
    try:
        empresa_uuid = UUID(empresa_id)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="ID de empresa no válido"
        )
    
    empresa = await get_empresa_by_id(db, empresa_uuid)
    
    if not empresa:
        raise HTTPException(
            status_code=404, 
            detail="Empresa no encontrada"
        )
    
    return empresa