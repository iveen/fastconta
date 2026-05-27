# app/api/v1/endpoints/auth.py
import asyncio
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text

from app.db.session import get_db
from app.models.global_models import User, Tenant
from app.schemas.auth import LoginRequest, TokenResponse, SignupRequest, SignupResponse
from app.core.security import verify_password, create_access_token, get_password_hash  # Asegúrate de importar tu haseador

# Importamos la función de migraciones de tu servicio de tenants
from app.services.tenant_service import ejecutar_migraciones_nuevo_tenant

router = APIRouter()

@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest, db: AsyncSession = Depends(get_db)):
    """
    Endpoint asíncrono para registrar un nuevo Tenant (Despacho/Cliente) 
    junto con su primer usuario Administrador y desplegar su esquema ofuscado.
    """
    # 1. Validaciones previas en el esquema public (Email y NIT únicos)
    email_check = await db.execute(select(User).where(User.email == request.admin_email))
    if email_check.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado.")
        
    nit_check = await db.execute(select(Tenant).where(Tenant.nit == request.nit))
    if nit_check.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="El NIT ya está registrado para otro tenant.")

    # 2. Preparar IDs y nombres de esquema blindados (Ofuscación por UUID)
    tenant_id = uuid.uuid4()
    schema_seguro = f"t_{tenant_id.hex}"
    user_id = uuid.uuid4()

    try:
        # 3. Crear el registro del Tenant en public
        nuevo_tenant = Tenant(
            id=tenant_id,
            name=request.tenant_name,
            schema_name=schema_seguro,
            nit=request.nit,
            plan="freemium",
            is_active=True
        )
        db.add(nuevo_tenant)

        # 4. Crear el esquema físico en la base de datos de forma asíncrona
        # Al usar variables internas sanitizadas (hex), evitamos inyección SQL
        await db.execute(text(f'CREATE SCHEMA "{schema_seguro}";'))

        # 5. Crear el usuario administrador asociado a este nuevo tenant
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

        # Confirmamos los cambios en el esquema public y la creación del esquema físico
        await db.commit()

    except Exception as e:
        await db.rollback()
        # Fallback de seguridad: si falló algo antes de Alembic, nos aseguramos de no dejar esquemas huérfanos
        try:
            await db.execute(text(f'DROP SCHEMA IF EXISTS "{schema_seguro}" CASCADE;'))
            await db.commit()
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error crítico al inicializar las entidades del tenant: {str(e)}"
        )

    # 6. Ejecutar las migraciones de Alembic sobre el nuevo esquema
    # Como los comandos de Alembic son síncronos y bloqueantes, los ejecutamos en un hilo separado
    # para mantener la naturaleza no bloqueante de FastAPI.
    try:
        await asyncio.to_thread(ejecutar_migraciones_nuevo_tenant, schema_seguro)
    except Exception as e:
        # Si Alembic truena, hacemos rollback drástico: eliminamos el tenant y el usuario para evitar entornos corruptos
        async with db.begin():
            await db.execute(text(f'DROP SCHEMA IF EXISTS "{schema_seguro}" CASCADE;'))
            await db.execute(text(f'DELETE FROM public.users WHERE id = :id'), {"id": user_id})
            await db.execute(text(f'DELETE FROM public.tenants WHERE id = :id'), {"id": tenant_id})
            await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"El entorno del tenant se creó pero las tablas fallaron en inicializarse: {str(e)}"
        )

    return SignupResponse(
        tenant_id=tenant_id,
        schema_name=schema_seguro,
        admin_user_id=user_id,
        message="Entorno multi-tenant e inicialización de administrador creados con éxito."
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    # ... Tu código de login actual se mantiene exactamente igual ...
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inactivo")

    token_data = {
        "sub": str(user.id),
        "role": user.role,
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
        role=user.role
    )