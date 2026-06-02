import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    DataScope,
    get_data_scope,
    get_password_hash,
    require_role,
    require_write_access,
)
from app.db.session import get_public_db
from app.models.global_models import Role, Tenant, User, UserEmpresa
from app.schemas.user import EmpresaAssignRequest, UserCreateRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])

ALLOWED_TENANT_ROLES = {"tenant_manager", "tenant_member", "tenant_client"}


@router.post(
    "/{user_id}/empresas",
    dependencies=[
        Depends(require_role("tenant_manager", "superadmin")),
        Depends(require_write_access)
    ]
)
async def assign_empresa_to_user(
    user_id: UUID,
    payload: EmpresaAssignRequest,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    # 1. Validar usuario objetivo
    res_user = await db.execute(select(User).where(User.id == user_id))
    target_user = res_user.scalar_one_or_none()
    if not target_user or not target_user.tenant_id:
        raise HTTPException(404, "Usuario no encontrado o sin tenant")

    tenant_id = target_user.tenant_id

    # 2. Obtener schema del tenant de forma segura
    res_tenant = await db.execute(
        text("SELECT schema_name FROM public.tenants WHERE id = :tid"),
        {"tid": str(tenant_id)}
    )
    tenant_row = res_tenant.first()
    if not tenant_row:
        raise HTTPException(404, "Tenant no encontrado")
    
    schema_name = tenant_row[0]
    # 🔒 Validación básica contra inyección SQL en search_path
    if not schema_name.isalnum() and "_" not in schema_name:
        raise HTTPException(500, "Schema con formato inválido")

    # 3. Validar que la empresa existe en el schema del tenant
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    res_emp = await db.execute(
        text("SELECT 1 FROM empresas WHERE id = :eid LIMIT 1"),
        {"eid": str(payload.empresa_id)}
    )
    if not res_emp.first():
        raise HTTPException(404, "La empresa no existe en este tenant")

    # 4. Restaurar search_path a public para insertar en user_empresas
    await db.execute(text("SET LOCAL search_path TO public"))
    
    # Evitar duplicados
    res_exists = await db.execute(
        select(UserEmpresa).where(
            UserEmpresa.user_id == user_id,
            UserEmpresa.tenant_id == tenant_id,
            UserEmpresa.empresa_id == payload.empresa_id,
            UserEmpresa.activo is True
        )
    )
    if res_exists.scalar_one_or_none():
        raise HTTPException(409, "Esta empresa ya está asignada al usuario")

    # Crear asignación
    assignment = UserEmpresa(
        user_id=user_id,
        tenant_id=tenant_id,
        empresa_id=payload.empresa_id,
        activo=True
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)

    return {
        "status": "asignado",
        "user_id": str(user_id),
        "empresa_id": str(payload.empresa_id),
        "tenant_id": str(tenant_id)
    }

@router.post(
    "/",
    dependencies=[
        Depends(require_role("superadmin", "tenant_manager"))
    ]
)
async def create_user(
    payload: UserCreateRequest,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    # 1️⃣ Validar que el rol solicitado es permitido para tenants
    if payload.role not in ALLOWED_TENANT_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Rol no permitido. Use uno de: {', '.join(ALLOWED_TENANT_ROLES)}"
        )

    # 2️⃣ Determinar tenant_id objetivo según quién ejecuta la acción
    if scope.role_code == "superadmin":
        if not payload.tenant_id:
            raise HTTPException(400, "Superadmin debe especificar tenant_id en la petición")
        target_tenant_id = payload.tenant_id
    elif scope.role_code == "tenant_manager":
        # 🔒 Un manager solo puede crear usuarios en SU PROPIO tenant
        target_tenant_id = scope.tenant_id
    else:
        raise HTTPException(403, "Rol no autorizado para crear usuarios")
    
    # Query ORM
    tenant_stmt = select(Tenant).where(Tenant.id == target_tenant_id, Tenant.is_active.is_(True))
    tenant_res = await db.execute(tenant_stmt)
    tenant = tenant_res.scalar_one_or_none()

    if not tenant:
        raise HTTPException(404, "Tenant no encontrado o inactivo")

    # 4️⃣ Normalizar email y verificar duplicados
    clean_email = payload.email.strip().lower()
    email_stmt = select(User).where(User.email == clean_email)
    if (await db.execute(email_stmt)).scalar_one_or_none():
        raise HTTPException(409, "El email ya está registrado en el sistema")
    
    role_stmt = select(Role).where(Role.codigo == payload.role)
    role_res = await db.execute(role_stmt)
    role_obj = role_res.scalar_one_or_none()
    if not role_obj:
        raise HTTPException(400, detail=f"Rol '{payload.role}' no existe")

    # 5️⃣ Crear y persistir usuario
    new_user = User(
        tenant_id=target_tenant_id,
        email=clean_email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name.strip(),
        role=role_obj,
        is_active=True
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # 6️⃣ Respuesta segura (sin password)
    return {
        "id": str(new_user.id),
        "email": new_user.email,
        "full_name": new_user.full_name,
        "role": new_user.role,
        "tenant_id": str(new_user.tenant_id),
        "is_active": new_user.is_active,
        "created_at": new_user.created_at.isoformat() if new_user.created_at else None
    }