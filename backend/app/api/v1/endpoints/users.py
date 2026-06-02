import logging
from uuid import UUID

from fastapi import (  # 👈 Query importado de fastapi
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
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
from app.db.session import get_public_db
from app.models.global_models import Role, Tenant, User, UserEmpresa
from app.schemas.user import EmpresaAssignRequest, UserCreateRequest

logger = logging.getLogger(__name__)  # ✅ Corregido: era logging.getLogger(name)
router = APIRouter(prefix="/users", tags=["users"])

ALLOWED_TENANT_ROLES = {"tenant_manager", "tenant_member", "tenant_client"}

# ==========================================
# 1. Listar usuarios del tenant (con filtro para superadmin)
# ==========================================
@router.get("/", response_model=list[dict])
async def list_users(
    tenant_id: str | None = Query(None),  # 👈 Simplificado para evitar conflictos de importación
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    if scope.role_code == "superadmin":
        if tenant_id:
            stmt = select(User).where(User.tenant_id == tenant_id).options(selectinload(User.tenant)).order_by(User.full_name)
        else:
            stmt = select(User).options(selectinload(User.tenant)).order_by(User.full_name)
    else:
        stmt = select(User).where(User.tenant_id == scope.tenant_id).options(selectinload(User.tenant)).order_by(User.full_name)
    
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    return [
        {
            "id": str(u.id),
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role.codigo if hasattr(u.role, 'codigo') else str(u.role),
            "tenant_id": str(u.tenant_id),
            "tenant_name": u.tenant.name if u.tenant else "N/A",
            "is_active": u.is_active
        }
        for u in users
    ]

# ==========================================
# 2. Obtener empresas asignadas a un usuario
# ==========================================
@router.get("/{user_id}/empresas", response_model=list[dict])
async def get_user_empresas(
    user_id: UUID,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db)
):
    res_user = await db.execute(select(User).where(User.id == user_id))
    user = res_user.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    
    if scope.role_code != "superadmin" and str(user.tenant_id) != str(scope.tenant_id):
        raise HTTPException(403, "Acceso denegado")

    res_assignments = await db.execute(
        select(UserEmpresa.empresa_id).where(
            UserEmpresa.user_id == user_id,
            UserEmpresa.activo.is_(True)  # ✅ Corrección: usar .is_(True) en lugar de == True
        )
    )
    empresa_ids = [str(row[0]) for row in res_assignments.fetchall()]
    if not empresa_ids:
        return []

    res_tenant = await db.execute(
        text("SELECT schema_name FROM public.tenants WHERE id = :tid"),
        {"tid": str(user.tenant_id)}
    )
    tenant_row = res_tenant.first()
    if not tenant_row:
        raise HTTPException(404, "Tenant no encontrado")
    
    schema_name = tenant_row[0]
    if not schema_name.replace("_", "").isalnum():
        raise HTTPException(500, "Schema con formato inválido")

    placeholders = ", ".join([f":eid_{i}" for i in range(len(empresa_ids))])
    params = {f"eid_{i}": eid for i, eid in enumerate(empresa_ids)}
    
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    res_empresas = await db.execute(
        text(f"SELECT id, nombre, nit FROM empresas WHERE id IN ({placeholders})"),
        params
    )
    
    return [
        {"empresa_id": str(row[0]), "nombre": row[1], "nit": row[2]}
        for row in res_empresas.fetchall()
    ]

# ==========================================
# 3. Asignar empresa a usuario
# ==========================================
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
    res_user = await db.execute(select(User).where(User.id == user_id))
    target_user = res_user.scalar_one_or_none()
    if not target_user or not target_user.tenant_id:
        raise HTTPException(404, "Usuario no encontrado o sin tenant")
    
    tenant_id = target_user.tenant_id
    res_tenant = await db.execute(
        text("SELECT schema_name FROM public.tenants WHERE id = :tid"),
        {"tid": str(tenant_id)}
    )
    tenant_row = res_tenant.first()
    if not tenant_row:
        raise HTTPException(404, "Tenant no encontrado")
    
    schema_name = tenant_row[0]
    if not schema_name.replace("_", "").isalnum():
        raise HTTPException(500, "Schema con formato inválido")

    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    res_emp = await db.execute(
        text("SELECT 1 FROM empresas WHERE id = :eid LIMIT 1"),
        {"eid": str(payload.empresa_id)}
    )
    if not res_emp.first():
        raise HTTPException(404, "La empresa no existe en este tenant")

    await db.execute(text("SET LOCAL search_path TO public"))
    
    res_exists = await db.execute(
        select(UserEmpresa).where(
            UserEmpresa.user_id == user_id,
            UserEmpresa.tenant_id == tenant_id,
            UserEmpresa.empresa_id == payload.empresa_id,
            UserEmpresa.activo.is_(True)  # ✅ Corrección: usar .is_(True)
        )
    )
    if res_exists.scalar_one_or_none():
        raise HTTPException(409, "Esta empresa ya está asignada al usuario")

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

# ==========================================
# 4. Crear usuario
# ==========================================
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

    if scope.role_code == "superadmin":
        if not payload.tenant_id:
            raise HTTPException(400, "Superadmin debe especificar tenant_id en la petición")
        target_tenant_id = payload.tenant_id
    elif scope.role_code == "tenant_manager":
        target_tenant_id = scope.tenant_id
    else:
        raise HTTPException(403, "Rol no autorizado para crear usuarios")

    tenant_stmt = select(Tenant).where(
        Tenant.id == target_tenant_id, 
        Tenant.is_active.is_(True)  # ✅ Corrección: usar .is_(True)
    )
    tenant_res = await db.execute(tenant_stmt)
    if not tenant_res.scalar_one_or_none():
        raise HTTPException(404, "Tenant no encontrado o inactivo")

    clean_email = payload.email.strip().lower()
    email_stmt = select(User).where(User.email == clean_email)
    if (await db.execute(email_stmt)).scalar_one_or_none():
        raise HTTPException(409, "El email ya está registrado en el sistema")

    role_stmt = select(Role).where(Role.codigo == payload.role)
    role_res = await db.execute(role_stmt)
    role_obj = role_res.scalar_one_or_none()
    if not role_obj:
        raise HTTPException(400, detail=f"Rol '{payload.role}' no existe")

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

    return {
        "id": str(new_user.id),
        "email": new_user.email,
        "full_name": new_user.full_name,
        "role": new_user.role.codigo if hasattr(new_user.role, 'codigo') else str(new_user.role),
        "tenant_id": str(new_user.tenant_id),
        "is_active": new_user.is_active,
        "created_at": new_user.created_at.isoformat() if new_user.created_at else None
    }