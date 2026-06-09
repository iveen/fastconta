# app/api/v1/endpoints/cierre.py
from typing import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import DataScope, get_data_scope
from app.db.base import AsyncSessionLocal  # ✅ CORRECCIÓN: Importar desde app.db.base
from app.services.cierre_contable import ejecutar_cierre_anual
from app.services.reversion_cierre import revertir_cierre_anual

router = APIRouter()

# ==============================================================================
# DEPENDENCIA SEGURA: Obtiene una sesión YA configurada para el esquema del tenant
# ==============================================================================
async def get_tenant_db_for_cierre(
    tenant_id_query: str | None = Query(None, alias="tenant_id", description="ID del tenant (requerido para superadmin)"),
    scope: DataScope = Depends(get_data_scope)
) -> AsyncGenerator[AsyncSession, None]:
    """
    Crea una sesión de base de datos y establece el search_path al esquema del tenant
    ANTES de cederla. Replica el patrón de cierre seguro de tu get_db().
    """
    # 1. Determinar a qué tenant debemos acceder
    if scope.role_code == "superadmin":
        if not tenant_id_query:
            raise HTTPException(status_code=400, detail="Superadmin debe especificar un tenant_id en los parámetros de la consulta.")
        target_tenant_id = tenant_id_query
    else:
        target_tenant_id = str(scope.tenant_id)

    # 2. Crear la sesión (usando tu factory real)
    session = AsyncSessionLocal()
    try:
        # Consultar el nombre del esquema en la BD pública
        res = await session.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"),
            {"tid": target_tenant_id}
        )
        row = res.first()
        if not row:
            raise HTTPException(status_code=404, detail="Tenant no encontrado")
        
        schema_name = row[0]
        
        # Validación de seguridad básica contra inyección SQL en el nombre del schema
        if not schema_name.replace("_", "").isalnum():
            raise HTTPException(status_code=500, detail="Nombre de esquema inválido")

        # Establecemos el search_path para esta transacción (SET LOCAL)
        await session.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
        
        session.info["current_user"] = {
            "schema": schema_name,
            "tenant_id": target_tenant_id,
            "role_code": scope.role_code
        }
        
        # 3. Cedemos la sesión YA configurada al endpoint
        yield session
        
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()  # 👈 CRÍTICO: Cierre seguro igual que en tu get_db()


# ==============================================================================
# ENDPOINT: Ejecutar Cierre Anual
# ==============================================================================
@router.post("/cierre-anual", response_model=dict, status_code=status.HTTP_201_CREATED)
async def cierre_anual(
    empresa_id: UUID = Query(..., description="ID de la empresa"),
    periodo_id: UUID = Query(..., description="ID del período fiscal a cerrar"),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_tenant_db_for_cierre)
):
    """
    Ejecuta el cierre contable anual.
    La dependencia 'get_tenant_db_for_cierre' YA configuró el search_path 
    y db.info["current_user"]["schema"]. El servicio lo lee directamente de ahí.
    """
    try:
        # Delegamos directamente. El servicio obtendrá el schema de db.info
        resultado = await ejecutar_cierre_anual(
            db=db,
            empresa_id=empresa_id,
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

# =========================================================================
# ENDPOINT 2: Revertir Cierre Anual
# =========================================================================
@router.post("/revertir-cierre", response_model=dict, status_code=status.HTTP_200_OK)
async def revertir_cierre(
    empresa_id: UUID = Query(..., description="ID de la empresa"),
    periodo_id: UUID = Query(..., description="ID del período fiscal a revertir"),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_tenant_db_for_cierre)
):
    if scope.role_code not in ["superadmin", "tenant_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: Se requiere rol de Administrador de Tenant o Superadmin."
        )

    try:
        # El servicio lee db.info["current_user"]["schema"] internamente
        resultado = await revertir_cierre_anual(
            db=db,
            empresa_id=empresa_id,
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