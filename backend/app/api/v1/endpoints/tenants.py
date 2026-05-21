from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from app.db.session import get_db
from app.models.global_models import Tenant, User, RegistrationAttempt
from app.core.tenant import create_tenant_schema
from app.schemas.tenant import TenantCreate, TenantResponse
from app.core.security import get_password_hash
from app.dependencies import require_role

router = APIRouter()

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