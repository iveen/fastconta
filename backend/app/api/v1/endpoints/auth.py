from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import get_db
from app.models.global_models import User, Tenant
from app.schemas.auth import LoginRequest, TokenResponse
from app.core.security import verify_password, create_access_token

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Buscar usuario por email
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inactivo")

    # Obtener el tenant asociado
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = tenant_result.scalar_one_or_none()
    if not tenant or not tenant.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant inactivo")

    # Construir payload del token
    access_token = create_access_token(data={
        "sub": str(user.id),
        "tenant_id": str(tenant.id),
        "schema": tenant.schema_name,
        "role": user.role,
        "email": user.email
    })

    return TokenResponse(
        access_token=access_token,
        tenant_name=tenant.name,
        role=user.role
    )