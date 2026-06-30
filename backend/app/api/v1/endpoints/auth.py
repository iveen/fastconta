# app/api/v1/endpoints/auth.py
import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.jwt_utils import create_access_token
from app.core.security import (  # Asegúrate de importar tu haseador
    get_current_user,
    get_password_hash,
    verify_password,
)
from app.db.session import get_db, get_tenant_db
from app.models.global_models import Tenant, User
from app.schemas.auth import LoginRequest, SignupRequest, SignupResponse, TokenResponse

# Importamos la función de migraciones de tu servicio de tenants
from app.services.tenant_setup import cleanup_tenant_schema, initialize_tenant_schema

router = APIRouter()

@router.get("/me")
async def get_current_user_info(
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna información del usuario autenticado.
    Usado por el frontend para restaurar la sesión al recargar.
    """
    tenant_name = None
    if current_user.tenant_id:
        # Forzar schema public para consultar tenants
        await db.execute(text("SET LOCAL search_path TO public"))
        tenant_result = await db.execute(
            select(Tenant).where(Tenant.id == current_user.tenant_id)
        )
        tenant = tenant_result.scalar_one_or_none()
        tenant_name = tenant.name if tenant else None
    
    role_code = "tenant_member"
    if current_user.role:
        if hasattr(current_user.role, 'codigo'):
            role_code = current_user.role.codigo
        elif hasattr(current_user.role, 'code'):
            role_code = current_user.role.code
        elif hasattr(current_user.role, 'name'):
            role_code = current_user.role.name
        elif isinstance(current_user.role, str):
            role_code = current_user.role
    
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": role_code,  # ✅ Ahora es string, no objeto
        "tenant_name": tenant_name,
        "tenant_id": str(current_user.tenant_id) if current_user.tenant_id else None
    }

@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest, db: AsyncSession = Depends(get_db)):
    # 1. Validaciones únicas en 'public'
    email_check = await db.execute(select(User).where(User.email == request.admin_email))
    if email_check.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado.")
        
    nit_check = await db.execute(select(Tenant).where(Tenant.nit == request.nit))
    if nit_check.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="El NIT ya está registrado.")

    tenant_id = uuid.uuid4()
    schema_seguro = f"t_{tenant_id.hex}"
    user_id = uuid.uuid4()

    try:
        # 2. Crear Tenant y Admin en 'public'
        nuevo_tenant = Tenant(
            id=tenant_id,
            name=request.tenant_name,
            schema_name=schema_seguro,
            nit=request.nit,
            plan="freemium",
            is_active=True
        )
        db.add(nuevo_tenant)

        nuevo_admin = User(
            id=user_id,
            tenant_id=tenant_id,
            email=request.admin_email,
            hashed_password=get_password_hash(request.admin_password),
            full_name=request.admin_full_name,
            role="admin",
            is_active=True
        )
        db.add(nuevo_admin)
        
        # 3. Commit inicial (registra el tenant antes de migrar)
        await db.commit()

        # 4. Crear esquema físico y migrar (Bloqueante -> Thread separado)
        await asyncio.to_thread(initialize_tenant_schema, schema_seguro, "alembic_tenant.ini")

    except Exception as e:
        await db.rollback()
        # Limpieza de seguridad: elimina schema huérfano si falla Alembic
        try:
            await asyncio.to_thread(cleanup_tenant_schema, schema_seguro)
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al inicializar el entorno del tenant: {str(e)}"
        )

    return SignupResponse(
        tenant_id=tenant_id,
        schema_name=schema_seguro,
        admin_user_id=user_id,
        message="Entorno multi-tenant e inicialización creados con éxito."
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    await db.execute(text("SET LOCAL search_path TO public")) # Forzar uso de Esquema Públic para Login
    stmt = (
        select(User)
        .options(selectinload(User.role))   # 👈 Carga la relación role de forma eager
        .where(User.email == request.email)
    )
    result = await db.execute(statement=stmt)
    user = result.scalar_one_or_none()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inactivo")

    role_code = user.role.codigo if user.role else "tenant_member"

    token_data = {
        "sub": str(user.id),
        "role": role_code,
        "email": user.email
    }

    tenant_name = "Super Administrador"
    schema_name = None

    if user.tenant_id is not None:
        tenant_result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
        tenant = tenant_result.scalar_one_or_none()
        if not tenant or not tenant.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant inactivo")
        token_data["tenant_id"] = str(tenant.id)
        token_data["schema"] = tenant.schema_name
        tenant_name = tenant.name
        schema_name = tenant.schema_name

    access_token = create_access_token(data=token_data)

    return TokenResponse(
        access_token=access_token,
        tenant_name=tenant_name,
        role=role_code,
        full_name=user.full_name,
    )