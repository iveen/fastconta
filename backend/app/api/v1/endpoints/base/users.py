# app/api/v1/endpoints/users.py
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import (
    DataScope,
    get_data_scope,
    get_password_hash,
    require_role,
    require_write_access,
)
from app.core.tenant_limits import check_user_limit
from app.db.session import get_public_db
from app.models.global_models import Role, Tenant, User, UserEmpresa
from app.schemas.base.user import EmpresaAssignRequest, UserCreateRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])

ALLOWED_TENANT_ROLES = {"tenant_manager", "tenant_member", "tenant_client"}


# ============================================================
# HELPERS
# ============================================================
async def _resolve_user_by_public_id(db: AsyncSession, public_id: UUID) -> User:
    """Helper para resolver un usuario por su public_id."""
    result = await db.execute(select(User).where(User.public_id == public_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    return user


async def _resolve_tenant_by_public_id(db: AsyncSession, public_id: UUID) -> Tenant:
    """Helper para resolver un tenant por su public_id."""
    result = await db.execute(select(Tenant).where(Tenant.public_id == public_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(404, "Tenant no encontrado")
    return tenant


async def _resolve_empresa_by_public_id(
    db: AsyncSession, schema_name: str, public_id: UUID
) -> int:
    """Helper para resolver una empresa por su public_id y retornar el id (BIGINT)."""
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    result = await db.execute(
        text("SELECT id FROM empresas WHERE public_id = :pid LIMIT 1"),
        {"pid": str(public_id)}
    )
    row = result.first()
    if not row:
        raise HTTPException(404, "Empresa no encontrada")
    return row[0]


# ============================================================
# 1. Listar usuarios
# ============================================================
@router.get("/", response_model=list[dict])
async def list_users(
    tenant_id: UUID | None = Query(None, description="public_id del tenant (solo superadmin)"),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    if scope.role_code == "superadmin":
        if tenant_id:
            tenant = await _resolve_tenant_by_public_id(db, tenant_id)
            stmt = (
                select(User)
                .where(User.tenant_id == tenant.id)
                .options(selectinload(User.tenant))
                .order_by(User.full_name)
            )
        else:
            stmt = (
                select(User)
                .options(selectinload(User.tenant))
                .order_by(User.full_name)
            )
    else:
        stmt = (
            select(User)
            .where(User.tenant_id == scope.tenant_id)
            .options(selectinload(User.tenant))
            .order_by(User.full_name)
        )
    
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    return [
        {
            "id": str(u.public_id),  # ✅ Exponer public_id
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role.codigo if hasattr(u.role, 'codigo') else str(u.role),
            "tenant_id": str(u.tenant.public_id) if u.tenant else None,
            "tenant_name": u.tenant.name if u.tenant else "N/A",
            "is_active": u.is_active
        }
        for u in users
    ]


# ============================================================
# 2. Obtener empresas asignadas a un usuario
# ============================================================
@router.get("/{user_public_id}/empresas", response_model=list[dict])
async def get_user_empresas(
    user_public_id: UUID,  # ✅ Recibir public_id
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    user = await _resolve_user_by_public_id(db, user_public_id)
    
    if scope.role_code != "superadmin" and user.tenant_id != scope.tenant_id:
        raise HTTPException(403, "Acceso denegado")
    
    # ✅ CORREGIDO: is_active en lugar de activo
    res_assignments = await db.execute(
        select(UserEmpresa.empresa_id).where(
            UserEmpresa.user_id == user.id,
            UserEmpresa.is_active.is_(True)
        )
    )
    empresa_ids = [row[0] for row in res_assignments.fetchall()]
    
    if not empresa_ids:
        return []
    
    res_tenant = await db.execute(
        select(Tenant.schema_name).where(Tenant.id == user.tenant_id)
    )
    schema_name = res_tenant.scalar_one_or_none()
    
    if not schema_name:
        raise HTTPException(404, "Tenant no encontrado")
    
    placeholders = ", ".join([f":eid_{i}" for i in range(len(empresa_ids))])
    params = {f"eid_{i}": eid for i, eid in enumerate(empresa_ids)}
    
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    res_empresas = await db.execute(
        text(f"SELECT public_id, nombre, nit FROM empresas WHERE id IN ({placeholders})"),
        params
    )
    
    return [
        {
            "empresa_id": str(row[0]),  # ✅ public_id (UUID)
            "nombre": row[1],
            "nit": row[2]
        }
        for row in res_empresas.fetchall()
    ]


# ============================================================
# 3. Asignar empresa a usuario
# ============================================================
@router.post(
    "/{user_public_id}/empresas",
    dependencies=[
        Depends(require_role("tenant_manager", "superadmin")),
        Depends(require_write_access)
    ]
)
async def assign_empresa_to_user(
    user_public_id: UUID,
    payload: EmpresaAssignRequest,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    target_user = await _resolve_user_by_public_id(db, user_public_id)
    
    if not target_user.tenant_id:
        raise HTTPException(404, "Usuario sin tenant asignado")
    
    tenant_id = target_user.tenant_id
    
    res_tenant = await db.execute(
        select(Tenant.schema_name).where(Tenant.id == tenant_id)
    )
    schema_name = res_tenant.scalar_one_or_none()
    
    if not schema_name:
        raise HTTPException(404, "Tenant no encontrado")
    
    # ✅ CORREGIDO: Resolver public_id → id (BIGINT)
    empresa_id_bigint = await _resolve_empresa_by_public_id(
        db, schema_name, payload.empresa_id
    )
    
    await db.execute(text("SET LOCAL search_path TO public"))
    
    res_exists = await db.execute(
        select(UserEmpresa).where(
            UserEmpresa.user_id == target_user.id,
            UserEmpresa.tenant_id == tenant_id,
            UserEmpresa.empresa_id == empresa_id_bigint,
            UserEmpresa.is_active.is_(True)
        )
    )
    if res_exists.scalar_one_or_none():
        raise HTTPException(409, "Esta empresa ya está asignada al usuario")
    
    assignment = UserEmpresa(
        user_id=target_user.id,
        tenant_id=tenant_id,
        empresa_id=empresa_id_bigint,
        is_active=True
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    
    return {
        "status": "asignado",
        "user_id": str(target_user.public_id),
        "empresa_id": str(payload.empresa_id),
        "tenant_id": str(tenant_id)
    }


# ============================================================
# 4. Crear usuario (CON VALIDACIÓN DE LÍMITES)
# ============================================================
@router.post(
    "/",
    dependencies=[Depends(require_role("superadmin", "tenant_manager"))]
)
async def create_user(
    payload: UserCreateRequest,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    if payload.role not in ALLOWED_TENANT_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Rol no permitido. Use uno de: {', '.join(ALLOWED_TENANT_ROLES)}"
        )
    
    # ✅ CORREGIDO: Resolver tenant por public_id para obtener id (BIGINT)
    if scope.role_code == "superadmin":
        if not payload.tenant_id:
            raise HTTPException(400, "Superadmin debe especificar tenant_id")
        tenant = await _resolve_tenant_by_public_id(db, payload.tenant_id)
        target_tenant_id = tenant.id
    elif scope.role_code == "tenant_manager":
        target_tenant_id = scope.tenant_id
    else:
        raise HTTPException(403, "Rol no autorizado")
    
    # ✅ NUEVO: Validar límite de usuarios
    limit_check = await check_user_limit(db, target_tenant_id)
    
    if not limit_check["can_create"]:
        if limit_check["is_trial"]:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "trial_limit_reached",
                    "message": f"Has alcanzado el límite de {limit_check['max_allowed']} usuarios del trial",
                    "current_count": limit_check["current_count"],
                    "max_allowed": limit_check["max_allowed"],
                    "trial_expires": limit_check["trial_expires"].isoformat() if limit_check["trial_expires"] else None,
                    "upgrade_hint": "Contacta al administrador para extender el trial o hacer upgrade"
                }
            )
        else:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "user_limit_reached",
                    "message": f"El tenant ha alcanzado el límite de {limit_check['max_allowed']} usuarios",
                    "current_count": limit_check["current_count"],
                    "max_allowed": limit_check["max_allowed"],
                    "upgrade_hint": "Contacta al administrador para aumentar el límite"
                }
            )
    
    # Validar que el tenant esté activo
    tenant_stmt = select(Tenant).where(
        Tenant.id == target_tenant_id,
        Tenant.is_active.is_(True)
    )
    tenant_res = await db.execute(tenant_stmt)
    if not tenant_res.scalar_one_or_none():
        raise HTTPException(404, "Tenant no encontrado o inactivo")
    
    # Validar email único
    clean_email = payload.email.strip().lower()
    email_stmt = select(User).where(User.email == clean_email)
    if (await db.execute(email_stmt)).scalar_one_or_none():
        raise HTTPException(409, "El email ya está registrado")
    
    # Validar rol
    role_stmt = select(Role).where(Role.codigo == payload.role)
    role_res = await db.execute(role_stmt)
    role_obj = role_res.scalar_one_or_none()
    if not role_obj:
        raise HTTPException(400, f"Rol '{payload.role}' no existe")
    
    # ✅ CORREGIDO: role_id en lugar de role
    new_user = User(
        tenant_id=target_tenant_id,
        email=clean_email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name.strip(),
        role_id=role_obj.id,  # ✅ BIGINT
        is_active=True
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return {
        "id": str(new_user.public_id),
        "email": new_user.email,
        "full_name": new_user.full_name,
        "role": new_user.role.codigo,
        "tenant_id": str(new_user.tenant_id),
        "is_active": new_user.is_active,
        "created_at": new_user.created_at.isoformat() if new_user.created_at else None,
        "limit_info": {
            "current_users": limit_check["current_count"] + 1,
            "max_users": limit_check["max_allowed"],
            "is_trial": limit_check["is_trial"]
        }
    }