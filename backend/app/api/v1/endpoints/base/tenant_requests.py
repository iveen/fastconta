"""Endpoints SuperAdmin para gestión de solicitudes de registro"""
import asyncio
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import DataScope, get_data_scope, get_password_hash
from app.db.session import get_db, get_public_db
from app.models.global_models import Role, Tenant, TenantRequest, User
from app.schemas.public.public_registration import (
    TenantApprovalPayload,
    TenantRequestListResponse,
)
from app.services.base.tenant_setup import (
    cleanup_tenant_schema,
    initialize_tenant_schema,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tenant-requests", tags=["Tenant Requests"])

# ============================================================
# 1. Listar solicitudes (con filtros)
# ============================================================
@router.get("/", response_model=list[TenantRequestListResponse])
async def list_tenant_requests(
    status_filter: str | None = Query(None, alias="status", description="Filtrar por estado"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    """Lista todas las solicitudes de registro (solo SuperAdmin)"""
    if scope.role_code != "superadmin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    stmt = select(TenantRequest).order_by(TenantRequest.created_at.desc())
    
    if status_filter:
        stmt = stmt.where(TenantRequest.status == status_filter)
    
    stmt = stmt.offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    requests = result.scalars().all()
    
    return [TenantRequestListResponse.model_validate(r) for r in requests]

# ============================================================
# 2. Contar solicitudes pendientes (para badge en UI)
# ============================================================
@router.get("/pending/count", response_model=dict)
async def count_pending_requests(
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    """Cuenta solicitudes pendientes (para badge en sidebar)"""
    if scope.role_code != "superadmin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    count = await db.scalar(
        select(func.count(TenantRequest.id)).where(
            TenantRequest.status == "pending"
        )
    )
    
    return {"pending_count": count or 0}

# ============================================================
# 3. Aprobar solicitud y crear tenant
# ============================================================
@router.post("/{request_id}/approve", response_model=dict, status_code=status.HTTP_201_CREATED)
async def approve_tenant_request(
    request_id: int,
    payload: TenantApprovalPayload,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_db)
):
    """
    Aprueba una solicitud y crea el tenant + admin.
    Solo SuperAdmin.
    
    ⚠️ CRÍTICO: Se hace commit del tenant ANTES de ejecutar migraciones
    para evitar deadlocks con las FKs a public.tenants.
    """
    if scope.role_code != "superadmin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # 1. Obtener solicitud
    result = await db.execute(
        select(TenantRequest).where(TenantRequest.id == request_id)
    )
    tenant_request = result.scalar_one_or_none()
    
    if not tenant_request:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    if tenant_request.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"La solicitud ya está {tenant_request.status}"
        )
    
    # 2. Validar que no exista tenant con ese NIT
    existing_tenant = await db.execute(
        select(Tenant).where(Tenant.nit == tenant_request.nit)
    )
    if existing_tenant.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="Ya existe un tenant con este NIT"
        )
    
    # 3. Validar que no exista usuario con ese email
    existing_user = await db.execute(
        select(User).where(User.email == payload.admin_email)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="Ya existe un usuario con este email"
        )
    
    # 4. Obtener rol tenant_manager
    role_result = await db.execute(
        select(Role).where(Role.codigo == "tenant_manager")
    )
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=500,
            detail="Rol 'tenant_manager' no encontrado. Ejecuta el seed."
        )
    
    # 5. Crear tenant con schema_name "pending" (placeholder)
    new_tenant = Tenant(
        name=tenant_request.company_name,
        nit=tenant_request.nit,
        schema_name="pending",  # Placeholder temporal
        plan=payload.plan,
        max_usuarios=payload.max_usuarios,
        admin_email=payload.admin_email,
        is_active=True
    )
    
    if payload.trial_days and payload.trial_max_usuarios:
        from datetime import timedelta
        new_tenant.trial_until = datetime.utcnow() + timedelta(days=payload.trial_days)
        new_tenant.trial_max_usuarios = payload.trial_max_usuarios
    
    db.add(new_tenant)
    
    # 🔑 CRÍTICO: Commit AHORA para liberar locks sobre public.tenants
    # Si no se hace, Alembic se quedará esperando al crear FKs a public.tenants
    await db.commit()
    await db.refresh(new_tenant)
    
    # 6. Generar schema_name seguro
    safe_uuid = str(new_tenant.public_id).replace("-", "")
    schema_name = f"t_{safe_uuid}"
    
    logger.info(f"🏢 Tenant creado en BD: id={new_tenant.id}, schema={schema_name}")
    
    # 7. Ejecutar migraciones (ya no hay locks pendientes)
    
    try:
        logger.info(f"🚀 Iniciando creación del schema '{schema_name}'...")
        
        # Timeout de 5 minutos para evitar bloqueos infinitos
        await asyncio.wait_for(
            asyncio.to_thread(initialize_tenant_schema, schema_name),
            timeout=300
        )
        logger.info(f"✅ Schema '{schema_name}' creado y migrado exitosamente")
    except asyncio.TimeoutError:
        logger.error(f"❌ Timeout creando schema '{schema_name}'")
        # Rollback: eliminar el tenant huérfano
        await db.delete(new_tenant)
        await db.commit()
        raise HTTPException(
            status_code=504,
            detail="Timeout al crear el schema. Intenta nuevamente."
        )
    except Exception as e:
        logger.error(f"❌ Error creando schema '{schema_name}': {e}", exc_info=True)
        # Rollback: eliminar el tenant huérfano
        await db.delete(new_tenant)
        await db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Error al inicializar el tenant: {str(e)}"
        )
    
    # 8. Actualizar schema_name del tenant
    new_tenant.schema_name = schema_name
    await db.commit()
    
    # 9. Crear usuario admin del tenant
    try:
        admin_user = User(
            tenant_id=new_tenant.id,
            email=payload.admin_email,
            hashed_password=get_password_hash(payload.admin_password),
            full_name=payload.admin_full_name,
            role_id=role.id,
            is_active=True
        )
        db.add(admin_user)
        
        # 10. Actualizar solicitud como aprobada
        tenant_request.status = "approved"
        tenant_request.reviewed_by = scope.user.id
        tenant_request.reviewed_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"✅ Solicitud {request_id} aprobada. Tenant: {new_tenant.name}, Admin: {admin_user.email}")
        
        return {
            "message": "Solicitud aprobada exitosamente",
            "tenant_id": str(new_tenant.public_id),
            "tenant_name": new_tenant.name,
            "admin_email": admin_user.email,
            "schema_name": schema_name
        }
    except Exception as e:
        logger.error(f"❌ Error creando admin: {e}", exc_info=True)
        # Rollback: eliminar el schema y el tenant
        try:
            await asyncio.to_thread(cleanup_tenant_schema, schema_name)
        except Exception as cleanup_err:
            logger.error(f"⚠️ Error en rollback de schema: {cleanup_err}")
        
        await db.delete(new_tenant)
        await db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear el usuario admin: {str(e)}"
        )