# app/api/v1/endpoints/users.py
import datetime
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.email.service import email_service
from app.core.security import (
    DataScope,
    calculate_password_expiration,
    get_current_user,
    get_data_scope,
    get_password_hash,
    require_role,
    require_write_access,
    validate_password_strength,
    verify_password,
)
from app.db.session import get_db, get_public_db
from app.models.global_models import Role, Tenant, User, UserEmpresa
from app.schemas.auth import ChangePasswordRequest
from app.schemas.base.user import (
    EmpresaAssignRequest,
    UserCreate,
    UserListResponse,
    UserResponse,
)

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
@router.get("/", response_model=list[UserListResponse])
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
    
    return users


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
@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_db),
):
    """
    Crea un nuevo usuario y envía email con contraseña temporal.
    Solo tenant_manager o superadmin.
    """
    # Validar permisos
    if scope.role_code not in ["superadmin", "tenant_manager"]:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # Validar que el email no exista
    existing_user = await db.execute(select(User).where(User.email == payload.email))
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Ya existe un usuario con este email")
    
    # Determinar tenant_id
    if scope.role_code == "superadmin":
        tenant_id = payload.tenant_id
        if not tenant_id:
            raise HTTPException(status_code=400, detail="Superadmin debe especificar tenant_id")
    else:
        tenant_id = scope.tenant_id
    
    # Obtener rol
    role_result = await db.execute(select(Role).where(Role.codigo == payload.role))
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=400, detail=f"Rol '{payload.role}' no encontrado")
    
    # ✅ Generar contraseña segura automáticamente
    from app.core.security import (
        calculate_password_expiration,
        generate_secure_password,
    )
    temp_password = generate_secure_password(length=16)
    password_expires_at = calculate_password_expiration(days=90)
    
    # Crear usuario
    new_user = User(
        tenant_id=tenant_id,
        email=payload.email,
        hashed_password=get_password_hash(temp_password),
        full_name=payload.full_name,
        role_id=role.id,
        is_active=True,
        must_change_password=True,  # ✅ Forzar cambio en primer login
        password_changed_at=datetime.datetime.now(datetime.timezone.utc),
        password_expires_at=password_expires_at,
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # ✅ Enviar email con credenciales
    try:
        from app.core.email.service import email_service
        await email_service.send_new_user_credentials(
            to=new_user.email,
            full_name=new_user.full_name,
            temp_password=temp_password,
            login_url=f"{settings.APP_URL}/login",
        )
        logger.info(f"📧 Email con credenciales enviado a {new_user.email}")
    except Exception as e:
        logger.error(f"️ No se pudo enviar email de credenciales: {e}")
        # No fallar la operación si el email falla
    
    return UserResponse.model_validate(new_user)

@router.post("/{user_id}/reset-password", response_model=dict)
async def admin_reset_user_password(
    user_id: UUID,  # ✅ Cambiar de int a UUID
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_db),
):
    """
    Un admin resetea la contraseña de un usuario y le envía email.
    Solo tenant_manager (de su tenant) o superadmin.
    """
    if scope.role_code not in ["superadmin", "tenant_manager"]:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # Buscar usuario por public_id (UUID)
    result = await db.execute(select(User).where(User.public_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Validar que sea del mismo tenant (si no es superadmin)
    if scope.role_code != "superadmin" and user.tenant_id != scope.tenant_id:
        raise HTTPException(status_code=403, detail="No puedes resetear usuarios de otro tenant")
    
    # No permitir que se resetee a sí mismo
    if user.id == scope.user.id:
        raise HTTPException(
            status_code=400, 
            detail="No puedes resetear tu propia contraseña. Usa la opción 'Cambiar mi contraseña' en el menú de usuario."
        )
    
    # ✅ Generar nueva contraseña
    from app.core.security import (
        calculate_password_expiration,
        generate_secure_password,
        get_password_hash,
    )
    new_password = generate_secure_password(length=16)
    password_expires_at = calculate_password_expiration(days=90)
    
    # Actualizar usuario
    user.hashed_password = get_password_hash(new_password)
    user.must_change_password = True  # Forzar cambio
    user.password_changed_at = datetime.datetime.now(datetime.timezone.utc)
    user.password_expires_at = password_expires_at
    user.is_locked = False
    user.locked_until = None
    user.failed_login_attempts = 0
    
    await db.commit()
    
    # ✅ Enviar email
    try:
        from app.core.email.service import email_service
        await email_service.send_password_reset(
            to=user.email,
            full_name=user.full_name,
            new_password=new_password,
        )
        logger.info(f"🔑 Contraseña reseteada y enviada a {user.email}")
    except Exception as e:
        logger.error(f"⚠️ No se pudo enviar email de reset: {e}")
        raise HTTPException(status_code=500, detail="Error al enviar email de reset")
    
    return {
        "message": f"Contraseña reseteada y enviada a {user.email}",
        "must_change_password": True,
    }

@router.post("/me/change-password", response_model=dict)
async def change_my_password(
    payload: ChangePasswordRequest,  # {current_password, new_password}
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    El usuario cambia SU PROPIA contraseña.
    Requiere validar la contraseña actual.
    """
    # 1. Validar contraseña actual
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta")
    
    # 2. Validar que sea diferente
    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=400, detail="La nueva contraseña debe ser diferente a la actual")
    
    # 3. Validar fortaleza
    password_errors = validate_password_strength(
        password=payload.new_password,
        user_email=current_user.email,
    )
    if password_errors:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "password_too_weak",
                "message": "La contraseña no cumple con los requisitos de seguridad",
                "errors": password_errors,
            }
        )
    
    # 4. Actualizar contraseña
    current_user.hashed_password = get_password_hash(payload.new_password)
    current_user.must_change_password = False
    current_user.is_locked = False
    current_user.locked_until = None
    current_user.failed_login_attempts = 0
    current_user.password_changed_at = datetime.datetime.now(datetime.timezone.utc)
    current_user.password_expires_at = calculate_password_expiration(days=90)
    
    await db.commit()

    try:
        await email_service.send_password_changed_notification(
            to=current_user.email,
            full_name=current_user.full_name,
        )
        logger.info(f"📧 Email de notificación enviado a {current_user.email}")
    except Exception as e:
        logger.error(f"⚠️ No se pudo enviar email de notificación: {e}")
    
    logger.info(f"✅ Usuario {current_user.email} cambió su contraseña exitosamente")
    
    return {
        "message": "Contraseña cambiada exitosamente",
        "password_expires_at": current_user.password_expires_at.isoformat(),
    }