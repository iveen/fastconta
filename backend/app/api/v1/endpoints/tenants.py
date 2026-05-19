from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.global_models import Tenant
from app.core.tenant import create_tenant_schema
from app.schemas.tenant import TenantCreate, TenantResponse
from app.core.security import get_password_hash
from app.models.global_models import User

router = APIRouter()

@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    payload: TenantCreate,
    db: AsyncSession = Depends(get_db)
):
    # Verificar si ya existe un tenant con ese nombre (o schema)
    from sqlalchemy import select
    result = await db.execute(select(Tenant).where(Tenant.name == payload.tenant_name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Ya existe un tenant con ese nombre")

    # Crear registro en tabla tenants
    new_tenant = Tenant(
        name=payload.tenant_name,
        schema_name=f"tenant_{payload.tenant_name.lower().replace(' ', '_')}",
        is_active=True
    )
    db.add(new_tenant)
    await db.flush()  # Para obtener el ID

    # Crear el schema correspondiente
    await create_tenant_schema(db, new_tenant.schema_name)

    # Crear usuario administrador para este tenant
    admin_user = User(
        tenant_id=new_tenant.id,
        email=payload.admin_email,
        hashed_password=get_password_hash(payload.admin_password),
        full_name="Administrador",
        role="admin",
        is_active=True
    )
    db.add(admin_user)
    await db.commit()

    return TenantResponse(
        id=new_tenant.id,
        name=new_tenant.name,
        schema_name=new_tenant.schema_name,
        created_at=new_tenant.created_at
    )