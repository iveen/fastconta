# app/api/v1/endpoints/cierre.py
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import DataScope, get_data_scope
from app.db.base import AsyncSessionLocal
from app.dependencies.empresa import get_active_empresa
from app.models.tenant_models import Empresa
from app.services.contabilidad.cierre_contable import ejecutar_cierre_anual
from app.services.contabilidad.reversion_cierre import revertir_cierre_anual

router = APIRouter()


# ============================================================
# DEPENDENCIA: Sesión configurada para el schema del tenant
# ============================================================
async def get_tenant_db_for_cierre(
    tenant_id_query: int | None = Query(None, alias="tenant_id", description="ID del tenant (requerido para superadmin)"),
    scope: DataScope = Depends(get_data_scope)
) -> AsyncGenerator[AsyncSession, None]:
    """Crea una sesión y establece el search_path al esquema del tenant."""
    if scope.role_code == "superadmin":
        if not tenant_id_query:
            raise HTTPException(status_code=400, detail="Superadmin debe especificar un tenant_id")
        target_tenant_id = tenant_id_query
    else:
        target_tenant_id = scope.tenant_id  # ✅ Ya es int

    session = AsyncSessionLocal()
    try:
        res = await session.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"),
            {"tid": target_tenant_id}  # ✅ int (no str)
        )
        row = res.first()
        if not row:
            raise HTTPException(status_code=404, detail="Tenant no encontrado")
        schema_name = row[0]
        if not schema_name.replace("_", "").isalnum():
            raise HTTPException(status_code=500, detail="Nombre de esquema inválido")
        await session.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
        session.info["current_user"] = {
            "schema": schema_name,
            "tenant_id": target_tenant_id,
            "role_code": scope.role_code
        }
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


# ============================================================
# 1. Ejecutar Cierre Anual
# ============================================================
@router.post("/cierre-anual", response_model=dict, status_code=status.HTTP_201_CREATED)
async def cierre_anual(
    empresa_id: int | None = Query(None, description="ID de la empresa"),  # ✅ BIGINT
    periodo_id: int = Query(..., description="ID del período fiscal a cerrar"),  # ✅ BIGINT
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_tenant_db_for_cierre),
    empresa_from_header: Empresa | None = Depends(get_active_empresa)
):
    try:
        empresa_id_final = empresa_id or (empresa_from_header.id if empresa_from_header else None)
        if not empresa_id_final:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo determinar la empresa para el cierre."
            )
        resultado = await ejecutar_cierre_anual(
            db=db,
            empresa_id=empresa_id_final,
            periodo_id=periodo_id
        )
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al ejecutar el cierre: {str(e)}"
        )


# ============================================================
# 2. Revertir Cierre Anual
# ============================================================
@router.post("/revertir-cierre", response_model=dict, status_code=status.HTTP_200_OK)
async def revertir_cierre(
    empresa_id: int | None = Query(None, description="ID de la empresa"),  # ✅ BIGINT
    periodo_id: int = Query(..., description="ID del período fiscal a revertir"),  # ✅ BIGINT
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_tenant_db_for_cierre),
    empresa_from_header: Empresa | None = Depends(get_active_empresa)
):
    if scope.role_code not in ["superadmin", "tenant_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: Se requiere rol de Administrador de Tenant o Superadmin."
        )
    try:
        empresa_id_final = empresa_id or (empresa_from_header.id if empresa_from_header else None)
        if not empresa_id_final:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo determinar la empresa para el cierre."
            )
        resultado = await revertir_cierre_anual(
            db=db,
            empresa_id=empresa_id_final,
            periodo_id=periodo_id
        )
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al revertir el cierre: {str(e)}"
        )