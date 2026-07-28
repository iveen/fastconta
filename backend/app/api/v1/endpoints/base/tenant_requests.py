"""Endpoints SuperAdmin para gestión de solicitudes de registro"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dispatcher import dispatch_tenant_job
from app.core.email.service import email_service
from app.core.security import (
    DataScope,
    calculate_password_expiration,
    generate_secure_password,
    get_data_scope,
    get_password_hash,
)
from app.db.session import get_db, get_public_db
from app.models.global_models import (
    BillingCycle,
    Role,
    SubscriptionStatus,
    Tenant,
    TenantRequest,
    TenantSubscription,
    User,
)
from app.schemas.base.tenant import (
    TenantApprovalPayload,
    TenantRejectionPayload,
    TenantRequestListResponse,
)
from app.services.base.tenant_setup import (
    cleanup_tenant_schema,
    initialize_tenant_schema,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tenant-requests", tags=["Tenant Requests"])

# ============================================================
# BACKGROUND TASK: Provisionamiento asíncrono
# ============================================================
# backend/app/api/v1/endpoints/tenant_requests.py


async def provision_tenant_background(
    tenant_id: int,
    user_id: int,
    schema_name: str,
    admin_email: str,
    admin_password: str,
    company_name: str,
    contact_name: str,
):
    """
    Tarea en segundo plano para ejecutar migraciones y notificar al usuario.
    Si falla, realiza rollback del schema y mantiene el tenant inactivo.
    """
    logger.info(f"🚀 [Background] Iniciando provisionamiento para schema '{schema_name}'")

    # ✅ Crear sesión de base de datos manualmente
    async for db in get_public_db():
        try:
            # 1. Ejecutar migraciones (síncrono, usar to_thread)
            await asyncio.to_thread(initialize_tenant_schema, schema_name)
            logger.info(f"✅ [Background] Migraciones completadas para '{schema_name}'")

            # 2. Activar tenant y usuario (las migraciones fueron exitosas)
            tenant = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one_or_none()
            if tenant:
                tenant.is_active = True
                logger.info(f"✅ [Background] Tenant {tenant_id} activado")

            user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
            if user:
                user.is_active = True
                logger.info(f"✅ [Background] User {user_id} activado")

            await db.commit()
            logger.info(f"✅ [Background] Tenant {tenant_id} y User {user_id} activados en BD")

            # 3. Enviar email con credenciales
            try:
                await email_service.send_tenant_aprobado(
                    to=admin_email,
                    company_name=company_name,
                    admin_email=admin_email,
                    admin_password=admin_password,
                    contact_name=contact_name,
                )
                logger.info(f"📧 [Background] Email de aprobación enviado a {admin_email}")
            except Exception as e:
                logger.error(f"⚠️ [Background] No se pudo enviar email de aprobación: {e}")

        except Exception as e:
            logger.error(f"❌ [Background] Error en provisionamiento para {schema_name}: {e}")
            try:
                # Rollback: desactivar registros y limpiar schema
                tenant = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one_or_none()
                if tenant:
                    tenant.is_active = False
                user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
                if user:
                    user.is_active = False
                await db.commit()

                # Limpiar schema fallido para no dejar basura en Postgres
                await asyncio.to_thread(cleanup_tenant_schema, schema_name)
                logger.info(f"🗑️ [Background] Rollback de schema '{schema_name}' completado")
            except Exception as cleanup_err:
                logger.error(f"❌ [Background] Error crítico en rollback: {cleanup_err}")
        finally:
            await db.close()


# ============================================================
# ENDPOINTS
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


@router.get("/pending/count", response_model=dict)
async def count_pending_requests(
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
):
    """Cuenta solicitudes pendientes (para badge en sidebar)"""
    if scope.role_code != "superadmin":
        raise HTTPException(status_code=403, detail="Acceso denegado")

    count = await db.scalar(select(func.count(TenantRequest.id)).where(TenantRequest.status == "pending"))
    return {"pending_count": count or 0}


# app/api/v1/endpoints/tenant_requests.py



@router.post("/{request_id}/approve", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def approve_tenant_request(
    request_id: int,
    payload: TenantApprovalPayload,  # Ahora incluye subscription_data
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_db),
):
    """
    Aprueba una solicitud, crea tenant + suscripción, y dispara background task.
    """
    if scope.role_code != "superadmin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # 1. Obtener solicitud
    result = await db.execute(select(TenantRequest).where(TenantRequest.id == request_id))
    tenant_request = result.scalar_one_or_none()
    if not tenant_request:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if tenant_request.status != "pending":
        raise HTTPException(status_code=400, detail=f"La solicitud ya está {tenant_request.status}")
    
    # 2. Validaciones de NIT y Email
    existing_tenant = await db.execute(select(Tenant).where(Tenant.nit == tenant_request.nit))
    if existing_tenant.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Ya existe un tenant con este NIT")
    
    existing_user = await db.execute(select(User).where(User.email == payload.admin_email))
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Ya existe un usuario con este email")
    
    # 3. Obtener rol
    role_result = await db.execute(select(Role).where(Role.codigo == "tenant_manager"))
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=500, detail="Rol 'tenant_manager' no encontrado")
    
    # 4. Crear tenant (INACTIVO)
    new_tenant = Tenant(
        name=tenant_request.company_name,
        nit=tenant_request.nit,
        schema_name="pending",
        admin_email=payload.admin_email,
        is_active=False,
    )
    db.add(new_tenant)
    await db.flush()
    
    # 5. Generar schema_name
    safe_uuid = str(new_tenant.public_id).replace("-", "")
    schema_name = f"t_{safe_uuid}"
    new_tenant.schema_name = schema_name
    await db.flush()
    
    # 6. 🆕 Crear suscripción inicial
    subscription_data = payload.subscription_data  # Del nuevo payload
    
    # Configuración por defecto según plan
    plan_configs = {
        "freemium": {"sessions": 1, "users": 3, "price_per_user": 0, "base_price": 0},
        "basico": {"sessions": 2, "users": subscription_data.max_users_registered, "price_per_user": 75, "base_price": 0},
        "profesional": {"sessions": 5, "users": subscription_data.max_users_registered, "price_per_user": 60, "base_price": 0},
        "empresarial": {"sessions": 10, "users": subscription_data.max_users_registered, "price_per_user": 45, "base_price": 0},
    }
    
    config = plan_configs[subscription_data.plan_type]
    now = datetime.now(UTC)
    trial_days = subscription_data.trial_days or (30 if subscription_data.plan_type == "freemium" else 14)
    
    subscription = TenantSubscription(
        tenant_id=new_tenant.id,
        plan_type=subscription_data.plan_type,
        max_concurrent_sessions=config["sessions"],
        max_users_registered=config["users"],
        price_per_user=config["price_per_user"],
        base_price=config["base_price"],
        billing_cycle=subscription_data.billing_cycle or BillingCycle.monthly.value,
        current_period_start=now,
        current_period_end=now + timedelta(days=trial_days),
        status=SubscriptionStatus.trial.value if trial_days > 0 else SubscriptionStatus.active.value,
        billing_email=payload.admin_email,
        nit_facturacion=tenant_request.nit,
    )
    subscription.total_monthly_price = subscription.calculate_total_price()
    db.add(subscription)
    
    # 7. Generar contraseña segura
    admin_password = generate_secure_password(length=16)
    password_expires_at = calculate_password_expiration(days=90)
    
    # 8. Crear usuario admin (INACTIVO)
    admin_user = User(
        tenant_id=new_tenant.id,
        email=payload.admin_email,
        hashed_password=get_password_hash(admin_password),
        full_name=payload.admin_full_name,
        role_id=role.id,
        is_active=False,
        must_change_password=True,
        password_changed_at=datetime.now(UTC),
        password_expires_at=password_expires_at,
    )
    db.add(admin_user)
    await db.flush()
    
    # 9. Actualizar solicitud como aprobada
    tenant_request.status = "approved"
    tenant_request.reviewed_by = scope.user.id
    tenant_request.reviewed_at = datetime.now(UTC)
    await db.commit()

    # 10 Dispatch Background Task
    dispatch_tenant_job(
        tenant_id=new_tenant.id,
        usier_id=admin_user.id,
        schema_name=schema_name,
        admin_email=admin_user.email,
        admin_password=admin_password,
        company_name=new_tenant.name,
        contact_name=payload.admin_full_name
    )
   
    return {
        "message": "Provisionamiento iniciado",
        "tenant_id": str(new_tenant.public_id),
        "subscription_id": subscription.id,
        "plan_type": subscription.plan_type,
        "trial_days": trial_days,
        "status": "provisioning",
    }


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

    result = await db.execute(select(TenantRequest).where(TenantRequest.id == request_id))
    tenant_request = result.scalar_one_or_none()

    if not tenant_request:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    if tenant_request.status != "pending":
        raise HTTPException(status_code=400, detail=f"La solicitud ya está {tenant_request.status}")

    tenant_request.status = "rejected"
    tenant_request.reviewed_by = scope.user.id
    tenant_request.reviewed_at = datetime.now(UTC)
    tenant_request.notes = f"Rechazada: {payload.reason}"

    await db.commit()
    logger.info(f"❌ Solicitud {request_id} rechazada: {payload.reason}")

    try:
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


@router.post("/{request_id}/resend-email", response_model=dict)
async def resend_request_email(
    request_id: int,
    payload: dict,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_db),
):
    """Reenvía el email de confirmación de solicitud. Permite actualizar el email."""
    if scope.role_code != "superadmin":
        raise HTTPException(status_code=403, detail="Acceso denegado")

    result = await db.execute(select(TenantRequest).where(TenantRequest.id == request_id))
    tenant_request = result.scalar_one_or_none()

    if not tenant_request:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    if tenant_request.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Solo se pueden reenviar emails de solicitudes pendientes (estado actual: {tenant_request.status})",
        )

    new_email = payload.get("contact_email")
    if new_email and new_email != tenant_request.contact_email:
        tenant_request.contact_email = new_email
        await db.commit()
        logger.info(f"📧 Email actualizado de {tenant_request.contact_email} a {new_email}")

    try:
        await email_service.send_solicitud_recibida(
            to=tenant_request.contact_email,
            company_name=tenant_request.company_name,
            contact_name=tenant_request.contact_name,
        )
        logger.info(f"📧 Email reenviado a {tenant_request.contact_email}")
    except Exception as e:
        logger.error(f" Error reenviando email: {e}")
        raise HTTPException(status_code=500, detail=f"Error al reenviar email: {str(e)}")

    return {
        "message": f"Email reenviado exitosamente a {tenant_request.contact_email}",
        "contact_email": tenant_request.contact_email,
    }


@router.post("/{request_id}/resend-credentials", response_model=dict)
async def resend_tenant_credentials(
    request_id: int,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_db),
):
    """
    Reenvía las credenciales de un tenant aprobado.
    Genera una NUEVA contraseña segura, actualiza el usuario admin
    y envía el email con las credenciales frescas.

    Solo SuperAdmin.
    """
    if scope.role_code != "superadmin":
        raise HTTPException(status_code=403, detail="Acceso denegado")

    # 1. Obtener solicitud
    result = await db.execute(select(TenantRequest).where(TenantRequest.id == request_id))
    tenant_request = result.scalar_one_or_none()

    if not tenant_request:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    # 2. Solo se puede reenviar credenciales de solicitudes aprobadas
    if tenant_request.status != "approved":
        raise HTTPException(
            status_code=400,
            detail=f"Solo se pueden reenviar credenciales de solicitudes aprobadas (estado actual: {tenant_request.status})",
        )

    # 3. Buscar el tenant asociado (por NIT)
    tenant_result = await db.execute(select(Tenant).where(Tenant.nit == tenant_request.nit))
    tenant = tenant_result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado para esta solicitud")

    # 4. Buscar el usuario admin del tenant
    user_result = await db.execute(
        select(User).where(
            User.tenant_id == tenant.id,
            User.email == tenant.admin_email,
        )
    )
    admin_user = user_result.scalar_one_or_none()

    if not admin_user:
        raise HTTPException(status_code=404, detail="Usuario admin no encontrado para este tenant")

    # 5. ✅ Generar NUEVA contraseña segura
    new_password = generate_secure_password(length=16)
    password_expires_at = calculate_password_expiration(days=90)

    # 6. ✅ Actualizar usuario con nueva contraseña
    admin_user.hashed_password = get_password_hash(new_password)
    admin_user.must_change_password = True  # Forzar cambio en primer login
    admin_user.password_changed_at = datetime.now(UTC)
    admin_user.password_expires_at = password_expires_at

    # También desbloquear por si estaba bloqueado
    admin_user.is_locked = False
    admin_user.locked_until = None
    admin_user.failed_login_attempts = 0

    await db.commit()

    logger.info(f"🔑 Nueva contraseña generada para admin {admin_user.email} (tenant: {tenant.name})")

    # 7. ✅ Enviar email con las nuevas credenciales
    try:
        from app.core.email.service import email_service

        await email_service.send_tenant_aprobado(
            to=admin_user.email,
            company_name=tenant.name,
            admin_email=admin_user.email,
            admin_password=new_password,
            contact_name=admin_user.full_name,
        )
        logger.info(f"📧 Email con nuevas credenciales enviado a {admin_user.email}")
    except Exception as e:
        logger.error(f"️ No se pudo enviar email con nuevas credenciales: {e}")
        # No revertimos la contraseña aunque falle el email (por seguridad, la anterior ya no sirve)

    return {
        "message": f"Nuevas credenciales generadas y enviadas a {admin_user.email}",
        "admin_email": admin_user.email,
        "tenant_name": tenant.name,
        "password_expires_at": password_expires_at.isoformat(),
    }
