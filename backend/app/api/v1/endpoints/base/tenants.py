# app/api/v1/endpoints/tenants.py

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import DataScope, get_data_scope, get_password_hash
from app.db.session import get_db, get_public_db
from app.dependencies import require_role
from app.models.global_models import (
    RegistrationAttempt,
    Role,
    SessionAudit,
    SubscriptionStatus,
    Tenant,
    TenantSubscription,
    User,
)
from app.schemas.base.tenant import (
    TenantCreate,
    TenantResponse,
    TenantTrialRequest,
    TenantUpgradeRequest,
)

router = APIRouter(prefix="/tenants", tags=["inquilinos"])
logger = logging.getLogger(__name__)

RESERVED_NAMES = {"sistema", "system", "public", "admin", "root"}


# ============================================================
# 1. Listar tenants
# ============================================================
@router.get("/", dependencies=[Depends(require_role("superadmin"))])
async def list_tenants(
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
):
    """Lista todos los tenants con información de suscripción activa."""
    if scope.role_code != "superadmin":
        raise HTTPException(status_code=403, detail="Acceso denegado")

    stmt = (
        select(Tenant)
        .where(Tenant.schema_name.notin_(["sistema", "system", "public"]))
        .order_by(Tenant.created_at.desc())
    )
    result = await db.execute(stmt)
    tenants = result.scalars().all()

    response = []
    for t in tenants:
        # Obtener suscripción activa
        sub_result = await db.execute(
            select(TenantSubscription).where(
                TenantSubscription.tenant_id == t.id,
                TenantSubscription.status.in_([
                    SubscriptionStatus.active.value,
                    SubscriptionStatus.trial.value
                ])
            )
        )
        subscription = sub_result.scalar_one_or_none()

        # Contar sesiones activas (últimos 15 min)
        cutoff = datetime.now(UTC) - timedelta(minutes=15)
        active_sessions = await db.scalar(
            select(func.count(SessionAudit.id)).where(
                SessionAudit.tenant_id == t.id,
                SessionAudit.is_active.is_(True),
                SessionAudit.last_activity >= cutoff,
            )
        )

        tenant_data = {
            "id": str(t.public_id),
            "name": t.name,
            "nit": t.nit,
            "schema_name": t.schema_name,
            "plan": t.plan,
            "is_active": t.is_active,
            "max_concurrent_sessions": t.max_concurrent_sessions,
            "max_users_registered": t.max_users_registered,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "active_subscription": None,
            "current_usage": {
                "active_sessions": active_sessions or 0,
            }
        }

        if subscription:
            tenant_data["active_subscription"] = {
                "plan_type": subscription.plan_type,
                "max_concurrent_sessions": subscription.max_concurrent_sessions,
                "max_users_registered": subscription.max_users_registered,
                "status": subscription.status,
                "current_period_end": subscription.current_period_end.isoformat(),
                "days_remaining": subscription.days_remaining,
                "monthly_price": float(subscription.total_monthly_price),
            }

        response.append(tenant_data)

    return response


# ============================================================
# 2. Crear tenant
# ============================================================
@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    payload: TenantCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("superadmin")),
):
    """Crea un nuevo tenant con su schema y migraciones."""
    # 0. Validar nombre del tenant (no reservado)
    if payload.tenant_name.strip().lower() in RESERVED_NAMES:
        raise HTTPException(status_code=400, detail=f"El nombre '{payload.tenant_name}' está reservado")

    # 1. Validar rol tenant_manager existe
    role_stmt = select(Role).where(Role.codigo == "tenant_manager")
    role_res = await db.execute(role_stmt)
    role_obj = role_res.scalar_one_or_none()
    if not role_obj:
        raise HTTPException(status_code=500, detail="Rol 'tenant_manager' no encontrado. Ejecuta el seed.")

    # 2. Validar unicidad NIT
    result = await db.execute(select(Tenant).where(Tenant.nit == payload.nit))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Ya existe un tenant con ese NIT")

    # 3. Validar unicidad del email admin
    email_stmt = select(User).where(User.email == payload.admin_email.strip().lower())
    if (await db.execute(email_stmt)).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="El email del administrador ya está registrado")

    # 4. Control anti-abuso por IP
    client_ip = request.client.host
    since = datetime.now(UTC) - timedelta(hours=24)
    attempts_count = await db.scalar(
        select(func.count(RegistrationAttempt.id)).where(
            RegistrationAttempt.ip_address == client_ip,
            RegistrationAttempt.created_at >= since
        )
    )
    if attempts_count >= 3:
        raise HTTPException(status_code=429, detail="Demasiados registros. Intente más tarde.")

    # 5. Crear tenant SIN schema_name aún (placeholder temporal)
    new_tenant = Tenant(
        name=payload.tenant_name,
        nit=payload.nit,
        schema_name="pending",
        plan=payload.plan or "freemium",
        max_concurrent_sessions=1,
        max_users_registered=3,
        admin_email=payload.admin_email,
        is_active=True,
    )
    db.add(new_tenant)
    await db.commit()
    await db.refresh(new_tenant)

    # 6. Generar schema_name
    safe_uuid = str(new_tenant.public_id).replace("-", "")
    schema_name = f"t_{safe_uuid}"
    new_tenant.schema_name = schema_name
    await db.flush()

    logger.info(f"Tenant creado en BD: id={new_tenant.id}, schema={schema_name}")

    # 7. Crear suscripción inicial (trial de 14 días)
    now = datetime.now(UTC)
    subscription = TenantSubscription(
        tenant_id=new_tenant.id,
        plan_type=payload.plan or "freemium",
        max_concurrent_sessions=1,
        max_users_registered=3,
        price_per_user=0,
        base_price=0,
        billing_cycle="mensual",
        current_period_start=now,
        current_period_end=now + timedelta(days=14),
        status=SubscriptionStatus.trial.value,
        billing_email=payload.admin_email,
        nit_facturacion=payload.nit,
    )
    subscription.total_monthly_price = subscription.calculate_total_price()
    db.add(subscription)

    # 8. Sincronizar campos efectivos del tenant
    new_tenant.sync_from_subscription()
    await db.commit()

    # 9. Crear schema y ejecutar migraciones
    import asyncio

    from app.services.base.tenant_setup import (
        cleanup_tenant_schema,
        initialize_tenant_schema,
    )

    try:
        logger.info(f"🚀 Iniciando creación del schema '{schema_name}'...")
        await asyncio.wait_for(
            asyncio.to_thread(initialize_tenant_schema, schema_name),
            300
        )
        logger.info(f"✅ Schema '{schema_name}' creado y migrado exitosamente")
    except TimeoutError:
        await db.delete(new_tenant)
        await db.commit()
        raise HTTPException(status_code=504, detail="Timeout al crear el schema")
    except Exception as e:
        logger.error(f"❌ Error creando schema '{schema_name}': {e}", exc_info=True)
        await db.delete(new_tenant)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Error al inicializar el tenant {str(e)}")

    # 10. Crear admin del tenant
    try:
        admin_user = User(
            tenant_id=new_tenant.id,
            email=payload.admin_email.strip().lower(),
            hashed_password=get_password_hash(payload.admin_password),
            full_name="Administrador",
            role_id=role_obj.id,
            is_active=True,
        )
        db.add(admin_user)
        db.add(RegistrationAttempt(ip_address=client_ip))
        await db.commit()
        await db.refresh(new_tenant)

        logger.info(f"✅ Tenant '{new_tenant.name}' creado exitosamente (schema: {schema_name})")

        return TenantResponse(
            id=new_tenant.public_id,
            name=new_tenant.name,
            schema_name=new_tenant.schema_name,
            nit=new_tenant.nit,
            plan=new_tenant.plan,
            max_usuarios=new_tenant.max_users_registered,
            is_active=new_tenant.is_active,
            created_at=new_tenant.created_at,
            admin_email=new_tenant.admin_email,
        )
    except Exception as e:
        logger.error(f"❌ Error creando admin: {e}", exc_info=True)
        try:
            await asyncio.to_thread(cleanup_tenant_schema, schema_name)
        except Exception as cleanup_err:
            logger.error(f"⚠️ Error en rollback: {cleanup_err}")
        await db.delete(new_tenant)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Error al crear el usuario admin: {str(e)}")


# ============================================================
# 3. Activar/Extender Trial
# ============================================================
@router.post("/{tenant_public_id}/trial", dependencies=[Depends(require_role("superadmin"))])
async def activate_tenant_trial(
    tenant_public_id: UUID,
    payload: TenantTrialRequest,
    db: AsyncSession = Depends(get_public_db),
):
    """
    Activa o extiende el trial de un tenant.
    Solo accesible para superadmin.
    """
    result = await db.execute(
        select(Tenant).where(Tenant.public_id == tenant_public_id)
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(404, "Tenant no encontrado")

    # Buscar suscripción activa
    sub_result = await db.execute(
        select(TenantSubscription).where(
            TenantSubscription.tenant_id == tenant.id,
            TenantSubscription.status.in_([
                SubscriptionStatus.active.value,
                SubscriptionStatus.trial.value
            ])
        )
    )
    subscription = sub_result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(404, "Suscripción activa no encontrada")

    # Calcular fecha de expiración del trial
    trial_until = datetime.now(UTC) + timedelta(days=payload.trial_days)

    # Actualizar suscripción con límites de trial
    subscription.status = SubscriptionStatus.trial.value
    subscription.current_period_end = trial_until
    subscription.max_concurrent_sessions = payload.trial_max_concurrent_sessions
    subscription.max_users_registered = payload.trial_max_users_registered
    subscription.total_monthly_price = subscription.calculate_total_price()

    # Sincronizar campos efectivos del tenant
    tenant.sync_from_subscription()

    await db.commit()
    await db.refresh(subscription)

    return {
        "status": "trial_activated",
        "tenant_id": str(tenant.public_id),
        "tenant_name": tenant.name,
        "trial_until": trial_until.isoformat(),
        "trial_max_concurrent_sessions": subscription.max_concurrent_sessions,
        "trial_max_users_registered": subscription.max_users_registered,
        "message": f"Trial activado por {payload.trial_days} días con {payload.trial_max_concurrent_sessions} sesiones concurrentes y {payload.trial_max_users_registered} usuarios",
    }


# ============================================================
# 4. Upgrade de Plan
# ============================================================
@router.post("/{tenant_public_id}/upgrade", dependencies=[Depends(require_role("superadmin"))])
async def upgrade_tenant(
    tenant_public_id: UUID,
    payload: TenantUpgradeRequest,
    db: AsyncSession = Depends(get_public_db),
):
    """
    Hace upgrade permanente del plan de un tenant.
    Solo accesible para superadmin.
    """
    result = await db.execute(
        select(Tenant).where(Tenant.public_id == tenant_public_id)
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(404, "Tenant no encontrado")

    # Obtener suscripción activa
    sub_result = await db.execute(
        select(TenantSubscription).where(
            TenantSubscription.tenant_id == tenant.id,
            TenantSubscription.status.in_([
                SubscriptionStatus.active.value,
                SubscriptionStatus.trial.value
            ])
        )
    )
    subscription = sub_result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(404, "Suscripción activa no encontrada")

    # Validar upgrades
    if payload.max_concurrent_sessions and payload.max_concurrent_sessions <= subscription.max_concurrent_sessions:
        raise HTTPException(
            400,
            f"El nuevo límite de sesiones ({payload.max_concurrent_sessions}) debe ser mayor al actual ({subscription.max_concurrent_sessions})"
        )

    if payload.max_users_registered and payload.max_users_registered <= subscription.max_users_registered:
        raise HTTPException(
            400,
            f"El nuevo límite de usuarios ({payload.max_users_registered}) debe ser mayor al actual ({subscription.max_users_registered})"
        )

    # Actualizar suscripción
    if payload.max_concurrent_sessions:
        subscription.max_concurrent_sessions = payload.max_concurrent_sessions
    if payload.max_users_registered:
        subscription.max_users_registered = payload.max_users_registered
    if payload.plan_type:
        subscription.plan_type = payload.plan_type

    subscription.total_monthly_price = subscription.calculate_total_price()

    # Sincronizar campos efectivos del tenant
    tenant.sync_from_subscription()

    await db.commit()
    await db.refresh(subscription)

    return {
        "status": "upgraded",
        "tenant_id": str(tenant.public_id),
        "subscription_id": subscription.id,
        "new_max_concurrent_sessions": subscription.max_concurrent_sessions,
        "new_max_users_registered": subscription.max_users_registered,
        "new_plan_type": subscription.plan_type,
        "new_monthly_price": float(subscription.total_monthly_price),
    }


# ============================================================
# 5. Uso del Tenant
# ============================================================
@router.get(
    "/{tenant_public_id}/usage",
    dependencies=[Depends(require_role("superadmin", "tenant_manager"))]
)
async def get_tenant_usage(
    tenant_public_id: UUID,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
):
    """
    Retorna el uso actual del tenant (sesiones, usuarios, suscripción).
    """
    # Validar permisos
    if scope.role_code == "tenant_manager":
        tenant_id = scope.tenant_id
    else:
        result = await db.execute(
            select(Tenant.id).where(Tenant.public_id == tenant_public_id)
        )
        tenant_id = result.scalar_one_or_none()
        if not tenant_id:
            raise HTTPException(404, "Tenant no encontrado")

    tenant = await db.get(Tenant, tenant_id)

    # Obtener suscripción activa
    sub_result = await db.execute(
        select(TenantSubscription).where(
            TenantSubscription.tenant_id == tenant_id,
            TenantSubscription.status.in_([
                SubscriptionStatus.active.value,
                SubscriptionStatus.trial.value
            ])
        )
    )
    subscription = sub_result.scalar_one_or_none()

    # Contar usuarios registrados
    user_count = await db.scalar(
        select(func.count(User.id)).where(
            User.tenant_id == tenant_id,
            User.is_active.is_(True)
        )
    )

    # Contar sesiones activas (últimos 15 min)
    cutoff = datetime.now(UTC) - timedelta(minutes=15)
    active_sessions = await db.scalar(
        select(func.count(SessionAudit.id)).where(
            SessionAudit.tenant_id == tenant_id,
            SessionAudit.is_active.is_(True),
            SessionAudit.last_activity >= cutoff,
        )
    )

    # Información de suscripción
    subscription_info = {}
    is_trial = False
    trial_expires = None

    if subscription:
        subscription_info = {
            "plan_type": subscription.plan_type,
            "max_concurrent_sessions": subscription.max_concurrent_sessions,
            "max_users_registered": subscription.max_users_registered,
            "status": subscription.status,
            "current_period_end": subscription.current_period_end.isoformat(),
            "days_remaining": subscription.days_remaining,
            "monthly_price": float(subscription.total_monthly_price),
        }

        if subscription.is_trial:
            is_trial = True
            trial_expires = subscription.current_period_end

    # Generar warnings
    warnings = []

    if subscription:
        session_usage_pct = (
            (active_sessions / subscription.max_concurrent_sessions * 100)
            if subscription.max_concurrent_sessions > 0 else 0
        )
        user_usage_pct = (
            (user_count / subscription.max_users_registered * 100)
            if subscription.max_users_registered > 0 else 0
        )

        if session_usage_pct >= 90:
            warnings.append("¡Crítico! Estás al 90%+ de tu límite de sesiones concurrentes")
        elif session_usage_pct >= 80:
            warnings.append("Estás cerca del límite de sesiones concurrentes")

        if user_usage_pct >= 90:
            warnings.append("¡Crítico! Estás al 90%+ de tu límite de usuarios registrados")
        elif user_usage_pct >= 80:
            warnings.append("Estás cerca del límite de usuarios registrados")

        if is_trial and trial_expires:
            days_left = (trial_expires - datetime.now(UTC)).days
            if days_left <= 7:
                warnings.append(f"Tu trial expira en {days_left} días")

    return {
        "tenant_id": str(tenant.public_id),
        "tenant_name": tenant.name,
        "subscription": subscription_info,
        "usage": {
            "active_sessions": {
                "actual": active_sessions or 0,
                "limite": subscription.max_concurrent_sessions if subscription else 0,
                "disponibles": max(0, (subscription.max_concurrent_sessions if subscription else 0) - (active_sessions or 0)),
                "porcentaje": round(session_usage_pct, 1) if subscription else 0,
            },
            "usuarios_registrados": {
                "actual": user_count or 0,
                "limite": subscription.max_users_registered if subscription else 0,
                "disponibles": max(0, (subscription.max_users_registered if subscription else 0) - (user_count or 0)),
                "porcentaje": round(user_usage_pct, 1) if subscription else 0,
            }
        },
        "trial": {"activo": is_trial, "expira": trial_expires.isoformat() if trial_expires else None},
        "warnings": warnings,
    }


# ============================================================
# 6. Desactivar Tenant (Soft Delete)
# ============================================================
@router.patch("/{tenant_public_id}/deactivate", response_model=dict)
async def deactivate_tenant(
    tenant_public_id: UUID,
    reason: str = Query(..., min_length=5, max_length=500),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
):
    """Desactiva un tenant (soft delete)"""
    if scope.role_code != "superadmin":
        raise HTTPException(status_code=403, detail="Acceso denegado")

    result = await db.execute(
        select(Tenant).where(Tenant.public_id == tenant_public_id)
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    if not tenant.is_active:
        raise HTTPException(status_code=400, detail="El tenant ya está inactivo")

    tenant.is_active = False
    tenant.deleted_at = datetime.now(UTC)

    await db.commit()
    logger.warning(f"️ Tenant desactivado: {tenant.name} (razón: {reason})")

    return {
        "message": "Tenant desactivado exitosamente",
        "tenant_id": str(tenant.public_id),
        "tenant_name": tenant.name,
        "reason": reason,
    }


# ============================================================
# 7. Reactivar Tenant
# ============================================================
@router.patch("/{tenant_public_id}/activate", response_model=dict)
async def activate_tenant(
    tenant_public_id: UUID,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
):
    """Reactiva un tenant previamente desactivado"""
    if scope.role_code != "superadmin":
        raise HTTPException(status_code=403, detail="Acceso denegado")

    result = await db.execute(
        select(Tenant).where(Tenant.public_id == tenant_public_id)
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    if tenant.is_active:
        raise HTTPException(status_code=400, detail="El tenant ya está activo")

    tenant.is_active = True
    tenant.deleted_at = None

    await db.commit()
    logger.info(f"✅ Tenant reactivado: {tenant.name}")

    return {
        "message": "Tenant reactivado exitosamente",
        "tenant_id": str(tenant.public_id),
        "tenant_name": tenant.name,
    }
