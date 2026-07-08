# app/core/tenant_limits.py

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.global_models import Tenant, User


async def get_tenant_user_limit(tenant: Tenant) -> int:
    """
    Determina el límite efectivo de usuarios para un tenant.
    
    Si está en trial y el trial no ha expirado, usa trial_max_usuarios.
    Si no, usa max_usuarios del plan.
    
    Args:
        tenant: Objeto Tenant
        
    Returns:
        int: Límite máximo de usuarios permitidos
    """
    # Verificar si está en trial activo
    if tenant.trial_until and tenant.trial_max_usuarios:
        now = datetime.utcnow()
        if tenant.trial_until > now:
            # Trial activo
            return tenant.trial_max_usuarios
    
    # Usar límite del plan
    return tenant.max_usuarios


async def check_user_limit(db: AsyncSession, tenant_id: int) -> dict:
    """
    Verifica si un tenant puede crear más usuarios.
    
    Args:
        db: Sesión de base de datos
        tenant_id: ID del tenant (BIGINT)
        
    Returns:
        dict: {
            "can_create": bool,
            "current_count": int,
            "max_allowed": int,
            "is_trial": bool,
            "trial_expires": datetime | None
        }
    """
    # Obtener tenant
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise ValueError("Tenant no encontrado")
    
    # Contar usuarios activos
    current_count = await db.scalar(
        select(func.count(User.id)).where(
            User.tenant_id == tenant_id,
            User.is_active.is_(True)
        )
    )
    
    # Determinar límite efectivo
    max_allowed = await get_tenant_user_limit(tenant)
    
    # Verificar si está en trial
    is_trial = False
    trial_expires = None
    if tenant.trial_until and tenant.trial_max_usuarios:
        now = datetime.utcnow()
        if tenant.trial_until > now:
            is_trial = True
            trial_expires = tenant.trial_until
    
    return {
        "can_create": current_count < max_allowed,
        "current_count": current_count,
        "max_allowed": max_allowed,
        "is_trial": is_trial,
        "trial_expires": trial_expires
    }