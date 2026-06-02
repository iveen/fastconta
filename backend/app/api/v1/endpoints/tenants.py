import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import DataScope, get_data_scope, get_password_hash
from app.core.tenant import create_tenant_schema
from app.db.session import get_db, get_public_db
from app.dependencies import require_role
from app.models.global_models import RegistrationAttempt, Tenant, User
from app.schemas.tenant import TenantCreate, TenantResponse

router = APIRouter()

logger = logging.getLogger(__name__)

@router.get("/", dependencies=[Depends(require_role("superadmin"))])
async def list_tenants(
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    if scope.role_code != "superadmin":
        raise HTTPException(status_code=403, detail="Acceso denegado")

    stmt = select(Tenant).order_by(Tenant.created_at.desc())
    result = await db.execute(stmt)
    tenants = result.scalars().all()

    return [
        {
            "id": str(t.id),
            "name": t.name,
            "nit": t.nit,
            "schema_name": t.schema_name,
            "plan": t.plan,
            "is_active": t.is_active,
            "max_empresas": t.max_empresas,
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t in tenants
    ]

@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    payload: TenantCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("superadmin"))   # <-- Solo superadmin
):
    # 1. Validar unicidad del NIT
    result = await db.execute(select(Tenant).where(Tenant.nit == payload.nit))
    if result.scalar_one_or_none():
        logger.error(f'Ya existe un tenant con el nit {payload.nit}')
        raise HTTPException(status_code=400, detail="Ya existe un tenant con ese NIT")

    # 2. Control anti-abuso por IP (máximo 3 registros en 24h)
    client_ip = request.client.host
    since = datetime.utcnow() - timedelta(hours=24)
    attempts_count = await db.scalar(
        select(func.count(RegistrationAttempt.id))
        .where(RegistrationAttempt.ip_address == client_ip,
               RegistrationAttempt.created_at >= since)
    )
    if attempts_count >= 3:
        logger.error(f'Demasiados intentos de registrar tenant {payload.tenant_name}, por favor Intente más tarde.')
        raise HTTPException(status_code=429, detail="Demasiados registros. Intente más tarde.")

    # 3. Crear tenant
    schema_name = f"tenant_{payload.tenant_name.lower().replace(' ', '_')}"
    new_tenant = Tenant(
        name=payload.tenant_name,
        schema_name=schema_name,
        nit=payload.nit,
        plan="freemium",
        max_empresas=5,
        is_active=True
    )
    db.add(new_tenant)
    await db.flush()

    # 4. Crear schema del tenant y tablas
    await create_tenant_schema(db, schema_name)

    # 5. Crear administrador del tenant
    admin_user = User(
        tenant_id=new_tenant.id,
        email=payload.admin_email,
        hashed_password=get_password_hash(payload.admin_password),
        full_name="Administrador",
        role="admin",
        is_active=True
    )
    db.add(admin_user)

    # 6. Registrar intento exitoso
    db.add(RegistrationAttempt(ip_address=client_ip))

    await db.commit()
    
    return TenantResponse(
        id=new_tenant.id,
        name=new_tenant.name,
        schema_name=new_tenant.schema_name,
        nit=new_tenant.nit,
        plan=new_tenant.plan,
        max_empresas=new_tenant.max_empresas,
        created_at=new_tenant.created_at
    )