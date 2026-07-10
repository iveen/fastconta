"""Endpoints SuperAdmin para gestión de solicitudes de registro"""
import asyncio
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    DataScope,
    calculate_password_expiration,
    generate_secure_password,
    get_data_scope,
    get_password_hash,
)
from app.db.session import get_db, get_public_db
from app.models.global_models import Role, Tenant, TenantRequest, User
from app.schemas.public.public_registration import (
    TenantApprovalPayload,
    TenantRejectionPayload,
    TenantRequestListResponse,
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
    db: AsyncSession = Depends(get_public_db),
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
    db: AsyncSession = Depends(get_public_db),
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
# 3. Aprobar solicitud y crear tenant (CON EMAIL + PASSWORD AUTO)
# ============================================================
@router.post("/{request_id}/approve", response_model=dict, status_code=status.HTTP_201_CREATED)
async def approve_tenant_request(
    request_id: int,
    payload: TenantApprovalPayload,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_db),
):
    """
    Aprueba una solicitud, crea tenant, genera password seguro y envía email.
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
        raise HTTPException(status_code=409, detail="Ya existe un tenant con este NIT")

    # 3. Validar que no exista usuario con ese email
    existing_user = await db.execute(
        select(User).where(User.email == payload.admin_email)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Ya existe un usuario con este email")

    # 4. Obtener rol tenant_manager
    role_result = await db.execute(
        select(Role).where(Role.codigo == "tenant_manager")
    )
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=500, detail="Rol 'tenant_manager' no encontrado")

    # 5. Crear tenant
    new_tenant = Tenant(
        name=tenant_request.company_name,
        nit=tenant_request.nit,
        schema_name="pending",
        plan=payload.plan,
        max_usuarios=payload.max_usuarios,
        admin_email=payload.admin_email,
        is_active=True,
    )
    if payload.trial_days and payload.trial_max_usuarios:
        new_tenant.trial_until = datetime.utcnow() + timedelta(days=payload.trial_days)
        new_tenant.trial_max_usuarios = payload.trial_max_usuarios

    db.add(new_tenant)
    await db.flush()

    # 6. Generar schema_name
    safe_uuid = str(new_tenant.public_id).replace("-", "")
    schema_name = f"t_{safe_uuid}"
    new_tenant.schema_name = schema_name
    await db.flush()

    logger.info(f" Tenant creado en BD: id={new_tenant.id}, schema={schema_name}")

    # 7. Crear schema y ejecutar migraciones
    from app.services.base.tenant_setup import (
        cleanup_tenant_schema,
        initialize_tenant_schema,
    )

    try:
        await asyncio.to_thread(initialize_tenant_schema, schema_name)
        logger.info(f"✅ Schema '{schema_name}' creado y migrado exitosamente")
    except Exception as e:
        logger.error(f"❌ Error creando schema '{schema_name}': {e}")
        try:
            await asyncio.to_thread(cleanup_tenant_schema, schema_name)
        except Exception as cleanup_err:
            logger.error(f"❌ Error en rollback: {cleanup_err}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al inicializar el tenant: {str(e)}")

    # 8. ✅ GENERAR PASSWORD SEGURO AUTOMÁTICAMENTE
    admin_password = generate_secure_password(length=16)
    password_expires_at = calculate_password_expiration(days=90)

    # 9. Crear usuario admin con política de contraseñas
    admin_user = User(
        tenant_id=new_tenant.id,
        email=payload.admin_email,
        hashed_password=get_password_hash(admin_password),
        full_name=payload.admin_full_name,
        role_id=role.id,
        is_active=True,
        must_change_password=True,  # ✅ Forzar cambio en primer login
        password_changed_at=datetime.utcnow(),
        password_expires_at=password_expires_at,
    )
    db.add(admin_user)

    # 10. Actualizar solicitud como aprobada
    tenant_request.status = "approved"
    tenant_request.reviewed_by = scope.user.id
    tenant_request.reviewed_at = datetime.utcnow()

    await db.commit()

    logger.info(f"✅ Solicitud {request_id} aprobada. Tenant: {new_tenant.name}, Admin: {admin_user.email}")

    # 11. ✅ ENVIAR EMAIL CON CREDENCIALES
    try:
        from app.core.email.service import email_service

        await email_service.send_tenant_aprobado(
            to=admin_user.email,
            company_name=new_tenant.name,
            admin_email=admin_user.email,
            admin_password=admin_password,
            contact_name=payload.admin_full_name,
        )
        logger.info(f"📧 Email de aprobación enviado a {admin_user.email}")
    except Exception as e:
        logger.error(f"⚠️ No se pudo enviar email de aprobación: {e}")
        # No fallar la operación si el email falla

    return {
        "message": "Solicitud aprobada exitosamente",
        "tenant_id": str(new_tenant.public_id),
        "tenant_name": new_tenant.name,
        "admin_email": admin_user.email,
        "schema_name": schema_name,
        "password_generated": True,
        "password_expires_at": password_expires_at.isoformat(),
    }


# ============================================================
# 4. Rechazar solicitud (CON EMAIL)
# ============================================================
@router.post("/{request_id}/reject", response_model=dict)
async def reject_tenant_request(
    request_id: int,
    payload: TenantRejectionPayload,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_db),
):
    """Rechaza una solicitud y envía email de notificación."""
    if scope.role_code != "superadmin":
        raise HTTPException(status_code=403, detail="Acceso denegado")

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

    tenant_request.status = "rejected"
    tenant_request.reviewed_by = scope.user.id
    tenant_request.reviewed_at = datetime.utcnow()
    tenant_request.notes = f"Rechazada: {payload.reason}"

    await db.commit()

    logger.info(f"❌ Solicitud {request_id} rechazada: {payload.reason}")

    # ✅ ENVIAR EMAIL DE RECHAZO
    try:
        from app.core.email.service import email_service

        await email_service.send_tenant_rechazado(
            to=tenant_request.contact_email,
            company_name=tenant_request.company_name,
            reason=payload.reason,
            contact_name=tenant_request.contact_name,
        )
        logger.info(f"📧 Email de rechazo enviado a {tenant_request.contact_email}")
    except Exception as e:
        logger.error(f"⚠️ No se pudo enviar email de rechazo: {e}")

    return {
        "message": "Solicitud rechazada",
        "request_id": request_id,
        "reason": payload.reason,
    }