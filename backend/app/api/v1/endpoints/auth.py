# app/api/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jwt_utils import create_access_token
from app.core.security import verify_password
from app.db.session import get_db
from app.models.global_models import Role, Tenant, User
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,  
    db: AsyncSession = Depends(get_db)
):
    # Buscar usuario por email
    stmt = select(User).where(User.email == login_data.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )
    
    # Cargar tenant
    tenant_stmt = select(Tenant).where(Tenant.id == user.tenant_id)
    tenant_res = await db.execute(tenant_stmt)
    tenant = tenant_res.scalar_one_or_none()
    
    # Cargar rol
    role_stmt = select(Role).where(Role.id == user.role_id)
    role_res = await db.execute(role_stmt)
    role = role_res.scalar_one_or_none()
    
    # Crear token
    access_token = create_access_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        role=role.codigo if role else "unknown",
        schema=tenant.schema_name if tenant else "public",
        tenant_name=tenant.name if tenant else "N/A"
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "tenant_name": tenant.name if tenant else None,
        "role": role.codigo if role else None,
        "full_name": user.full_name,
        "email": user.email
    }