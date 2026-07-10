# app/api/endpoints/auth.py
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jwt_utils import create_access_token
from app.core.security import (
    MAX_LOGIN_ATTEMPTS,
    DataScope,
    calculate_password_expiration,
    clear_failed_attempts,
    generate_secure_password,
    get_current_user,
    get_data_scope,
    get_lock_remaining_minutes,
    get_password_hash,
    is_password_expired,
    is_user_locked,
    register_failed_attempt,
    validate_password_strength,
    verify_password,
)
from app.db.session import get_db
from app.models.global_models import Role, Tenant, User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = logging.getLogger(__name__)


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Autenticación de usuario con política de bloqueo por intentos fallidos.
    
    Flujo:
    1. Buscar usuario por email
    2. Verificar si está bloqueado
    3. Verificar contraseña
    4. Si falla: incrementar intentos, bloquear si llega a 5
    5. Si éxito: limpiar intentos, verificar expiración
    6. Retornar token + flags de política
    """
    
    # 1. Buscar usuario por email
    stmt = select(User).where(User.email == login_data.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    # ✅ Si el usuario no existe, retornar error genérico (seguridad)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 2. ✅ Verificar si está bloqueado (y el bloqueo no ha expirado)
    if is_user_locked(user):
        remaining = get_lock_remaining_minutes(user)
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail={
                "error": "account_locked",
                "message": f"Cuenta bloqueada por {MAX_LOGIN_ATTEMPTS} intentos fallidos. "
                           f"Intente nuevamente en {remaining} minutos.",
                "locked_until": user.locked_until.isoformat() if user.locked_until else None,
                "remaining_minutes": remaining,
            }
        )
    
    # 3. Verificar contraseña
    if not verify_password(login_data.password, user.hashed_password):
        # ✅ Registrar intento fallido
        register_failed_attempt(user)
        await db.commit()
        
        remaining_attempts = MAX_LOGIN_ATTEMPTS - user.failed_login_attempts
        
        if user.is_locked:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail={
                    "error": "account_locked",
                    "message": f"Cuenta bloqueada por {MAX_LOGIN_ATTEMPTS} intentos fallidos. "
                               f"Se ha enviado un correo con instrucciones para restablecer su contraseña.",
                    "locked_until": user.locked_until.isoformat() if user.locked_until else None,
                    "remaining_minutes": get_lock_remaining_minutes(user),
                    "must_change_password": True,
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "invalid_credentials",
                    "message": "Email o contraseña incorrectos",
                    "remaining_attempts": remaining_attempts,
                    "warning": f"Atención: {remaining_attempts} intentos restantes antes del bloqueo." 
                              if remaining_attempts <= 2 else None,
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    # 4. ✅ Verificar si el usuario está activo
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo. Contacte al administrador.",
        )
    
    # 5. ✅ Verificar si el bloqueo expiró (debe cambiar password)
    lock_expired_needs_change = False
    if user.is_locked and user.locked_until and datetime.utcnow() > user.locked_until:
        lock_expired_needs_change = True
        # No limpiar is_locked aquí, se limpia al cambiar contraseña
    
    # 6. ✅ Login exitoso: limpiar intentos fallidos
    clear_failed_attempts(user)
    
    # 7. Verificar expiración de contraseña
    password_expired = is_password_expired(user)
    
    # Determinar si debe cambiar contraseña
    must_change = user.must_change_password or password_expired or lock_expired_needs_change
    
    if must_change:
        logger.info(f"⚠️ Usuario {user.email} debe cambiar contraseña "
                    f"(must_change={user.must_change_password}, "
                    f"expired={password_expired}, lock_expired={lock_expired_needs_change})")
    
    await db.commit()
    
    # 8. Cargar tenant y rol
    tenant_stmt = select(Tenant).where(Tenant.id == user.tenant_id)
    tenant_res = await db.execute(tenant_stmt)
    tenant = tenant_res.scalar_one_or_none()
    
    role_stmt = select(Role).where(Role.id == user.role_id)
    role_res = await db.execute(role_stmt)
    role = role_res.scalar_one_or_none()
    
    # 9. Crear token
    access_token = create_access_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        role=role.codigo if role else "unknown",
        schema=tenant.schema_name if tenant else "public",
        tenant_name=tenant.name if tenant else "N/A"
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        tenant_name=tenant.name if tenant else None,
        role=role.codigo if role else None,
        full_name=user.full_name,
        email=user.email,
        must_change_password=must_change,
        password_expires_at=user.password_expires_at.isoformat() if user.password_expires_at else None,
    )

@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cambia la contraseña del usuario actual.
    Valida la fortaleza de la nueva contraseña.
    """
    # 1. Validar contraseña actual
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta")
    
    # 2. Validar que sea diferente
    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=400, detail="La nueva contraseña debe ser diferente a la actual")
    
    # 3. ✅ NUEVO: Validar fortaleza de la contraseña
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
    current_user.password_changed_at = datetime.utcnow()
    current_user.password_expires_at = calculate_password_expiration(days=90)
    
    await db.commit()
    
    logger.info(f"✅ Usuario {current_user.email} cambió su contraseña exitosamente")
    
    return {
        "message": "Contraseña cambiada exitosamente",
        "password_expires_at": current_user.password_expires_at.isoformat(),
        "account_unlocked": True,
    }


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    user_id: int,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_db)
):
    """
    Resetea la contraseña de un usuario y envía email con la nueva.
    También desbloquea la cuenta si estaba bloqueada.
    """
    if scope.role_code not in ["superadmin", "tenant_manager"]:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if scope.role_code != "superadmin" and user.tenant_id != scope.tenant_id:
        raise HTTPException(status_code=403, detail="No puedes resetear contraseñas de otros tenants")
    
    # Generar nueva contraseña
    new_password = generate_secure_password(length=16)
    
    # ✅ Actualizar usuario
    user.hashed_password = get_password_hash(new_password)
    user.must_change_password = True
    user.password_changed_at = datetime.utcnow()
    user.password_expires_at = calculate_password_expiration(days=90)
    
    # ✅ Desbloquear cuenta
    user.is_locked = False
    user.locked_until = None
    user.failed_login_attempts = 0
    
    await db.commit()
    
    logger.info(f"🔑 Contraseña reseteada para usuario {user.email}")
    
    # Enviar email
    try:
        from app.core.email.service import email_service
        await email_service.send_password_reset(
            to=user.email,
            full_name=user.full_name,
            new_password=new_password,
        )
        logger.info(f"📧 Email de reset enviado a {user.email}")
    except Exception as e:
        logger.error(f"⚠️ No se pudo enviar email de reset: {e}")
    
    return {
        "message": "Contraseña reseteada exitosamente",
        "user_email": user.email,
        "must_change_password": True,
        "account_unlocked": True,
    }