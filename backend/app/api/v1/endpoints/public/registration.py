"""Endpoints públicos para registro de tenants"""
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.global_models import RegistrationAttempt, Tenant, TenantRequest
from app.schemas.public.public_registration import (
    TenantRequestCreate,
    TenantRequestResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/public", tags=["Public Registration"])

@router.post("/register", response_model=TenantRequestResponse, status_code=status.HTTP_201_CREATED)
async def public_register(
    payload: TenantRequestCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Registro público de solicitud de tenant.
    No requiere autenticación.
    """
    # 1. Rate limiting por IP (máximo 3 registros por IP en 24h)
    client_ip = request.client.host
    since = datetime.utcnow() - timedelta(hours=24)
    
    attempts_count = await db.scalar(
        select(func.count(RegistrationAttempt.id))
        .where(
            RegistrationAttempt.ip_address == client_ip,
            RegistrationAttempt.created_at >= since
        )
    )
    
    if attempts_count >= 3:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados registros desde tu IP. Intenta más tarde."
        )
    
    # 2. Validar que no exista un tenant activo con ese NIT
    existing_tenant = await db.execute(
        select(Tenant).where(
            Tenant.nit == payload.nit,
            Tenant.is_active.is_(True)
        )
    )
    
    if existing_tenant.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una cuenta activa con este NIT."
        )
    
    # 3. Validar que no exista una solicitud pendiente con ese NIT o email
    existing_request = await db.execute(
        select(TenantRequest).where(
            (TenantRequest.nit == payload.nit) | (TenantRequest.contact_email == payload.contact_email),
            TenantRequest.status.in_(["pending", "approved"])
        )
    )
    
    if existing_request.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una solicitud activa con este NIT o email."
        )
    
    # 4. Crear solicitud
    tenant_request = TenantRequest(
        company_name=payload.company_name,
        nit=payload.nit,
        contact_name=payload.contact_name,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
        regimen_fiscal_id=payload.regimen_fiscal_id,
        estimated_clients_count=payload.estimated_clients_count,
        notes=payload.notes,
        status="pending"
    )
    
    db.add(tenant_request)
    
    # 5. Registrar intento (para rate limiting)
    db.add(RegistrationAttempt(ip_address=client_ip))
    
    await db.commit()
    await db.refresh(tenant_request)
    
    logger.info(f"✅ Nueva solicitud de registro: {tenant_request.company_name} (NIT: {tenant_request.nit})")
    
    return TenantRequestResponse(
        id=tenant_request.id,
        public_id=tenant_request.public_id,
        company_name=tenant_request.company_name,
        nit=tenant_request.nit,
        contact_name=tenant_request.contact_name,
        contact_email=tenant_request.contact_email,
        status=tenant_request.status,
        created_at=tenant_request.created_at,
        message="Solicitud recibida. Será revisada en 24-48h hábiles."
    )