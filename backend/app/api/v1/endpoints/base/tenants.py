# app/api/endpoints/tenants.py
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import DataScope, get_data_scope, get_password_hash
from app.db.session import get_db, get_public_db
from app.dependencies import require_role
from app.models.global_models import RegistrationAttempt, Role, Tenant, User
from app.schemas.base.tenant import (
    TenantCreate,
    TenantResponse,
    TenantTrialRequest,
    TenantUpgradeRequest,
)

router = APIRouter(prefix="/tenants", tags=["inquilinos"])
logger = logging.getLogger(__name__)

# Nombres reservados que no pueden usarse como tenant
RESERVED_NAMES = {"sistema", "system", "public", "admin", "root"}


# ============================================================
# 1. Listar tenants
# ============================================================
@router.get("/", dependencies=[Depends(require_role("superadmin"))])
async def list_tenants(
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    """Lista todos los tenants (excluyendo el tenant 'system')."""
    if scope.role_code != "superadmin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # Filtrar tenants reservados
    stmt = select(Tenant).where(
        Tenant.schema_name.notin_(['sistema', 'system', 'public'])
    ).order_by(Tenant.created_at.desc())
    
    result = await db.execute(stmt)
    tenants = result.scalars().all()
    
    return [
        {
            "id": str(t.public_id),  # ✅ Exponer public_id (UUID)
            "name": t.name,
            "nit": t.nit,
            "schema_name": t.schema_name,
            "plan": t.plan,
            "is_active": t.is_active,
            "max_usuarios": t.max_usuarios,  # ✅ Ya no max_empresas
            "trial_until": t.trial_until.isoformat() if t.trial_until else None,
            "trial_max_usuarios": t.trial_max_usuarios,
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t in tenants
    ]


# ============================================================
# 2. Crear tenant
# ============================================================
@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    payload: TenantCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("superadmin"))
):
    """Crea un nuevo tenant con su schema y migraciones."""
    
    # 0. Validar nombre del tenant (no reservado)
    if payload.tenant_name.strip().lower() in RESERVED_NAMES:
        raise HTTPException(
            status_code=400,
            detail=f"El nombre '{payload.tenant_name}' está reservado"
        )
    
    # 1. Validar rol tenant_manager existe
    role_stmt = select(Role).where(Role.codigo == "tenant_manager")
    role_res = await db.execute(role_stmt)
    role_obj = role_res.scalar_one_or_none()
    
    if not role_obj:
        raise HTTPException(
            status_code=500,
            detail="Rol 'tenant_manager' no encontrado. Ejecuta el seed."
        )
    
    # 2. Validar unicidad NIT
    result = await db.execute(select(Tenant).where(Tenant.nit == payload.nit))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Ya existe un tenant con ese NIT")
    
    # 3. Validar unicidad del email admin
    email_stmt = select(User).where(User.email == payload.admin_email.strip().lower())
    if (await db.execute(email_stmt)).scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="El email del administrador ya está registrado"
        )
    
    # 4. Control anti-abuso por IP
    client_ip = request.client.host
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    attempts_count = await db.scalar(
        select(func.count(RegistrationAttempt.id))
        .where(
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
        schema_name="pending",  # ⚠️ Placeholder temporal
        plan=payload.plan or "freemium",
        max_usuarios=1,  # ✅ Límite inicial por defecto
        admin_email=payload.admin_email,
        is_active=True
    )
    db.add(new_tenant)
    await db.commit()
    await db.refresh(new_tenant)
        
    # 6. ✅ CORREGIDO: Generar schema_name con formato t_{public_id_sin_guiones}
    # Ejemplo: t_550e8400e29b41d4a716446655440000 (34 chars)
    safe_uuid = str(new_tenant.public_id).replace("-", "")
    schema_name = f"t_{safe_uuid}"
    new_tenant.schema_name = schema_name
    await db.flush()
    
    logger.info(f"Tenant creado en BD: id={new_tenant.id}, schema={schema_name}")
    
    # 7. Crear schema y ejecutar TODAS las migraciones
    # ⚠️ SÍNCRONO: debe ejecutarse en thread separado
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
    except asyncio.TimeoutError:
        await db.delete(new_tenant)
        await db.commit()
        raise HTTPException(status_code=504, detail="Timeout al crear el schema")
    except Exception as e:
        logger.error(f"❌ Error creando schema '{schema_name}': {e}", exc_info=True)
        await db.delete(new_tenant)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Error al inicializar el tenant {str(e)}")

    # 8. Actualizar schema_name del tenant
    new_tenant.schema_name = schema_name
    await db.commit()

    # 9. Crear admin del tenant
    try:
        admin_user = User(
            tenant_id=new_tenant.id,
            email=payload.admin_email.strip().lower(),
            hashed_password=get_password_hash(payload.admin_password),
            full_name="Administrador",
            role_id=role_obj.id,
            is_active=True
        )
        db.add(admin_user)
        
        # 10. Registrar intento exitoso
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
            max_usuarios=new_tenant.max_usuarios,
            is_active=new_tenant.is_active,
            created_at=new_tenant.created_at,
            admin_email=new_tenant.admin_email
        )
    except Exception as e:
        logger.error(f"❌ Error creando admin: {e}", exc_info=True)
        try:
            await asyncio.to_thread(cleanup_tenant_schema, schema_name)
        except Exception as cleanup_err:
            logger.error(f"⚠️ Error en rollback: {cleanup_err}")
        
        await db.delete(new_tenant)
        await db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear el usuario admin: {str(e)}"
        )

# ============================================================
# 3. Activar/Extender Trial
# ============================================================
@router.post("/{tenant_public_id}/trial", dependencies=[Depends(require_role("superadmin"))])
async def activate_tenant_trial(
    tenant_public_id: UUID,
    payload: TenantTrialRequest,
    db: AsyncSession = Depends(get_public_db)
):
    """
    Activa o extiende el trial de un tenant.
    Solo accesible para superadmin.
    """
    # Buscar tenant por public_id
    result = await db.execute(
        select(Tenant).where(Tenant.public_id == tenant_public_id)
    )
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(404, "Tenant no encontrado")
    
    # Calcular fecha de expiración
    trial_until = datetime.now(timezone.utc) + timedelta(days=payload.trial_days)
    
    # Actualizar trial
    tenant.trial_until = trial_until
    tenant.trial_max_usuarios = payload.trial_max_usuarios
    
    await db.commit()
    await db.refresh(tenant)
    
    return {
        "status": "trial_activated",
        "tenant_id": str(tenant.public_id),
        "tenant_name": tenant.name,
        "trial_until": trial_until.isoformat(),
        "trial_max_usuarios": tenant.trial_max_usuarios,
        "message": f"Trial activado por {payload.trial_days} días con límite de {payload.trial_max_usuarios} usuarios"
    }


# ============================================================
# 4. Upgrade de Plan
# ============================================================
@router.post(
    "/{tenant_public_id}/upgrade",
    dependencies=[Depends(require_role("superadmin"))]
)
async def upgrade_tenant(
    tenant_public_id: UUID,
    payload: TenantUpgradeRequest,
    db: AsyncSession = Depends(get_public_db)
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
    
    # Validar que el nuevo límite sea mayor al actual
    if payload.max_usuarios <= tenant.max_usuarios:
        raise HTTPException(
            400,
            f"El nuevo límite ({payload.max_usuarios}) debe ser mayor al actual ({tenant.max_usuarios})"
        )
    
    # Actualizar plan
    tenant.max_usuarios = payload.max_usuarios
    tenant.plan = payload.plan
    
    await db.commit()
    await db.refresh(tenant)
    
    return {
        "status": "upgraded",
        "tenant_id": str(tenant.public_id),
        "new_max_usuarios": tenant.max_usuarios,
        "new_plan": tenant.plan,
        "message": f"Límite de usuarios aumentado a {tenant.max_usuarios}"
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
    db: AsyncSession = Depends(get_public_db)
):
    """
    Retorna el uso actual del tenant (usuarios, empresas, etc.)
    Útil para el dashboard del tenant_manager.
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
    
    # Obtener tenant
    tenant = await db.get(Tenant, tenant_id)
    
    # Contar usuarios activos
    user_count = await db.scalar(
        select(func.count(User.id)).where(
            User.tenant_id == tenant_id,
            User.is_active.is_(True)
        )
    )
    
    # Determinar límite efectivo (considerando trial)
    max_allowed = tenant.max_usuarios
    is_trial = False
    trial_expires = None
    
    if tenant.trial_until and tenant.trial_max_usuarios:
        now = datetime.now(timezone.utc)
        if tenant.trial_until > now:
            is_trial = True
            trial_expires = tenant.trial_until
            max_allowed = tenant.trial_max_usuarios
    
    # Generar warnings
    warnings = []
    usage_percentage = (user_count / max_allowed) * 100 if max_allowed > 0 else 0
    
    if usage_percentage >= 90:
        warnings.append("¡Crítico! Estás al 90%+ de tu límite de usuarios")
    elif usage_percentage >= 80:
        warnings.append("Estás cerca del límite de usuarios")
    
    if is_trial and tenant.trial_until:
        days_left = (tenant.trial_until - datetime.now(timezone.utc)).days
        if days_left <= 7:
            warnings.append(f"Tu trial expira en {days_left} días")
    
    return {
        "tenant_id": str(tenant.public_id),
        "tenant_name": tenant.name,
        "plan": tenant.plan,
        "usage": {
            "usuarios": {
                "actual": user_count,
                "limite": max_allowed,
                "disponibles": max(0, max_allowed - user_count),
                "porcentaje": round(usage_percentage, 1)
            }
        },
        "trial": {
            "activo": is_trial,
            "expira": trial_expires.isoformat() if trial_expires else None
        },
        "warnings": warnings
    }

# ============================================================
# 6. Desactivar Tenant (Soft Delete)
# ============================================================
@router.patch("/{tenant_public_id}/deactivate", response_model=dict)
async def deactivate_tenant(
    tenant_public_id: UUID,
    reason: str = Query(..., min_length=5, max_length=500),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
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
    tenant.deleted_at = datetime.now(timezone.utc)
    
    # TODO: Invalidar tokens JWT de usuarios de este tenant (requiere Redis)
    
    await db.commit()
    
    logger.warning(f"⚠️ Tenant desactivado: {tenant.name} (razón: {reason})")
    
    return {
        "message": "Tenant desactivado exitosamente",
        "tenant_id": str(tenant.public_id),
        "tenant_name": tenant.name,
        "reason": reason
    }

# ============================================================
# 7. Reactivar Tenant
# ============================================================
@router.patch("/{tenant_public_id}/activate", response_model=dict)
async def activate_tenant(
    tenant_public_id: UUID,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
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
        "tenant_name": tenant.name
    }