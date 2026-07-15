# app/api/endpoints/auth.py
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.email.service import email_service
from app.core.jwt_utils import create_access_token
from app.core.security import (
    MAX_LOGIN_ATTEMPTS,
    RESET_TOKEN_EXPIRATION_MINUTES,
    DataScope,
    calculate_password_expiration,
    clear_failed_attempts,
    generate_reset_token,
    generate_secure_password,
    get_current_user,
    get_data_scope,
    get_lock_remaining_minutes,
    get_password_hash,
    is_lock_expired,
    is_password_expired,
    is_user_locked,
    register_failed_attempt,
    reset_expired_lock,
    validate_password_strength,
    verify_password,
    verify_reset_token,
)
from app.db.session import get_db
from app.models.global_models import LoginAudit, PasswordResetToken, Role, Tenant, User
from app.schemas.auth import (
    ChangePasswordRequest,
    ConfirmPasswordResetRequest,
    ConfirmPasswordResetResponse,
    FirstLoginChangePasswordRequest,
    LoginAuditResponse,
    LoginAuditStats,
    LoginRequest,
    RequestPasswordResetRequest,
    RequestPasswordResetResponse,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = logging.getLogger(__name__)

@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
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

    # Capturar información del cliente
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # 1. Buscar usuario por email
    stmt = select(User).where(User.email == login_data.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    # ✅ Si el usuario no existe, retornar error genérico (seguridad)
    if not user:
        await log_login_attempt(
            db, None, login_data.email, ip_address, user_agent,
            "FAILED_USER_NOT_FOUND", "Usuario no encontrado en el sistema"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. ✅ NUEVO: Si el bloqueo expiró, resetear contador (dar 5 intentos nuevos)
    if is_lock_expired(user):
        reset_expired_lock(user)
        await db.commit()
        logger.info(f"🔓 Bloqueo expirado para {user.email}. Contador reseteado.")
    
    # 3. ✅ Verificar si está bloqueado (y el bloqueo no ha expirado)
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
    
    # 4. Verificar contraseña
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
 
    # 6. ✅ Login exitoso: limpiar intentos fallidos
    clear_failed_attempts(user)
    
    # 7. Verificar expiración de contraseña
    password_expired = is_password_expired(user)
    
    # Determinar si debe cambiar contraseña
    must_change = user.must_change_password or password_expired
    
    if must_change:
            logger.info(f"⚠️ Usuario {user.email} debe cambiar contraseña "
                        f"(must_change={user.must_change_password}, expired={password_expired})")
    
    await db.commit()

    # 8. Registrar login exitoso en bitácora
    await log_login_attempt(
        db, user.id, login_data.email, ip_address, user_agent,
        "SUCCESS", None
    )
    
    # 9. Cargar tenant y rol
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
        user_id=str(user.id),
        public_id=str(user.public_id),
        must_change_password=must_change,
        password_expires_at=user.password_expires_at.isoformat() if user.password_expires_at else None,
    )

@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # ... (toda la validación y actualización de contraseña que ya tienes) ...
    
    current_user.hashed_password = get_password_hash(payload.new_password)
    current_user.must_change_password = False
    current_user.is_locked = False
    current_user.locked_until = None
    current_user.failed_login_attempts = 0
    current_user.password_changed_at = datetime.now(timezone.utc)
    current_user.password_expires_at = calculate_password_expiration(days=90)
    await db.commit()

    # ✅ AGREGA ESTE BLOQUE AQUÍ (copiado de users.py)
    try:
        changed_at_formatted = current_user.password_changed_at.strftime("%d/%m/%Y %H:%M")
        await email_service.send_password_changed_notification(
            to=current_user.email,
            full_name=current_user.full_name,
            changed_at=changed_at_formatted,
        )
        logger.info(f"📧 Email de notificación enviado a {current_user.email}")
    except Exception as e:
        logger.error(f"⚠️ No se pudo enviar email de notificación: {e}")
        # No fallar la operación si el email falla, solo loguear

    logger.info(f"✅ Usuario {current_user.email} cambió su contraseña exitosamente")
    return {
        "message": "Contraseña cambiada exitosamente",
        "password_expires_at": current_user.password_expires_at.isoformat(),
        "account_unlocked": True,
    }

@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    user_id: UUID,  # ✅ 1. Recibe UUID
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_db)
):
    """
    Resetea la contraseña de un usuario y envía email con la nueva.
    También desbloquea la cuenta si estaba bloqueada.
    """
    if scope.role_code not in ["superadmin", "tenant_manager"]:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # ✅ 2. Buscar por public_id (UUID) en lugar de id (bigint)
    result = await db.execute(select(User).where(User.public_id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if scope.role_code != "superadmin" and user.tenant_id != scope.tenant_id:
        raise HTTPException(status_code=403, detail="No puedes resetear contraseñas de otros tenants")
    
    # ✅ 3. NUEVO: Evitar que el admin se resetee a sí mismo desde esta interfaz
    if user.id == scope.user.id:
        raise HTTPException(
            status_code=400,
            detail="No puedes resetear tu propia contraseña desde aquí. Usa la opción 'Cambiar Contraseña' en tu menú de usuario."
        )
    
    # Generar nueva contraseña
    new_password = generate_secure_password(length=16)
    
    # Actualizar usuario
    user.hashed_password = get_password_hash(new_password)
    user.must_change_password = True
    user.password_changed_at = datetime.now(timezone.utc)  # ✅ Usar timezone-aware
    user.password_expires_at = calculate_password_expiration(days=90)
    
    # Desbloquear cuenta
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


# ============================================================
# PASSWORD RESET (Self-Service con Token)
# ============================================================
MAX_RESET_REQUESTS_PER_HOUR = 100


@router.post("/request-password-reset", response_model=RequestPasswordResetResponse)
async def request_password_reset(
    payload: RequestPasswordResetRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Solicita un email con token para resetear contraseña.
    
    Por seguridad, SIEMPRE retorna success aunque el email no exista,
    para no revelar qué emails están registrados.
    """
    # 1. Buscar usuario
    result = await db.execute(
        select(User).where(User.email == payload.email, User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # No revelamos si el email existe o no
        logger.warning(f"Solicitud de reset para email inexistente: {payload.email}")
        return RequestPasswordResetResponse(
            message="Si el email existe, recibirás un correo con instrucciones."
        )
    
    # 2. Rate limiting: max 3 solicitudes por email por hora
    since = datetime.now(timezone.utc) - timedelta(hours=1)
    recent_tokens = await db.scalar(
        select(func.count(PasswordResetToken.id))
        .where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.created_at >= since,
        )
    )
    
    if recent_tokens >= MAX_RESET_REQUESTS_PER_HOUR:
        # Por seguridad no revelamos que hay rate-limit
        return RequestPasswordResetResponse(
            message="Si el email existe, recibirás un correo con instrucciones."
        )
    
    # 3. Invalidar tokens anteriores no usados del mismo usuario
    await db.execute(
        PasswordResetToken.__table__.update()
        .where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.is_used.is_(False),
        )
        .values(is_used=True, used_at=datetime.now(timezone.utc))
    )
    
    # 4. Generar token nuevo
    plain_token, token_hash = generate_reset_token()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRATION_MINUTES)
    
    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        ip_address=request.client.host if request.client else None,
    )
    
    db.add(reset_token)
    await db.commit()
    
    # 5. Enviar email con token
    try:
        from app.core.email.config import email_config
        from app.core.email.service import email_service
        reset_url = f"{email_config.app_url}/reset-password?token={plain_token}"
        
        await email_service.send_password_reset_request(
            to=user.email,
            full_name=user.full_name,
            reset_url=reset_url,
        )
        logger.info(f"📧 Email de reset con token enviado a {user.email}")
    except Exception as e:
        logger.error(f"⚠️ Error enviando email de reset: {e}")
    
    # Siempre mismo mensaje, exista o no el email
    return RequestPasswordResetResponse(
        message="Si el email existe, recibirás un correo con instrucciones."
    )


@router.post("/confirm-password-reset", response_model=ConfirmPasswordResetResponse)
async def confirm_password_reset(
    payload: ConfirmPasswordResetRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Confirma un reset de contraseña usando el token del email.
    
    Valida:
    - Token existe
    - Token no ha expirado
    - Token no ha sido usado
    - Nueva contraseña es fuerte
    """
    # 1. Buscar token activo
    result = await db.execute(
        select(PasswordResetToken)
        .where(
            PasswordResetToken.is_used.is_(False),
        )
        .options(selectinload(PasswordResetToken.user))
    )
    tokens = result.scalars().all()
    
    # Por seguridad: mismo mensaje para cualquier error
    generic_error = "Token inválido o expirado"
    
    # 2. Validar token hash
    valid_token = None
    for t in tokens:
        if verify_reset_token(payload.token, t.token_hash):
            valid_token = t
            break
    
    if not valid_token:
        raise HTTPException(status_code=400, detail=generic_error)
    
    # 3. Validar expiración
    if datetime.now(timezone.utc) > valid_token.expires_at:
        raise HTTPException(status_code=400, detail=generic_error)
    
    user = valid_token.user
    
    # 4. Validar que el usuario exista y esté activo
    if not user or not user.is_active:
        raise HTTPException(status_code=400, detail=generic_error)
    
    # 5. Validar fortaleza de la nueva contraseña
    password_errors = validate_password_strength(
        password=payload.new_password,
        user_email=user.email,
    )
    
    if password_errors:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "password_too_weak",
                "message": "La contraseña no cumple con los requisitos",
                "errors": password_errors,
            }
        )
    
    # 6. Marcar token como usado
    valid_token.is_used = True
    valid_token.used_at = datetime.now(timezone.utc)
    
    # 7. Actualizar contraseña
    user.hashed_password = get_password_hash(payload.new_password)
    user.must_change_password = False
    user.password_changed_at = datetime.now(timezone.utc)
    user.password_expires_at = calculate_password_expiration(days=90)
    
    # 8. Desbloquear cuenta si estaba bloqueada
    user.is_locked = False
    user.locked_until = None
    user.failed_login_attempts = 0
    
    await db.commit()
    
    logger.info(f"🔑 Contraseña reseteada vía token para usuario {user.email}")
    
    return ConfirmPasswordResetResponse(
        message="Contraseña actualizada correctamente. Ya puedes iniciar sesión.",
        email=user.email,
    )

async def log_login_attempt(
    db: AsyncSession,
    user_id: int | None,
    email: str,
    ip_address: str,
    user_agent: str,
    status: str,
    failure_reason: str | None = None,
) -> None:
    """
    Registra un intento de login en la bitácora.
    
    Args:
        db: Sesión de base de datos
        user_id: ID del usuario (None si no existe)
        email: Email intentado
        ip_address: IP del cliente
        user_agent: User-Agent del navegador
        status: SUCCESS, FAILED_INVALID_PASSWORD, FAILED_LOCKED, FAILED_USER_NOT_FOUND, FAILED_INACTIVE
        failure_reason: Descripción del motivo de fallo (opcional)
    """
    try:
        audit = LoginAudit(
            user_id=user_id,
            email_attempted=email,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            failure_reason=failure_reason,
        )
        db.add(audit)
        await db.commit()
    except Exception as e:
        # No fallar el login si la bitácora falla
        logger.error(f"Error registrando en bitácora de login: {e}")


@router.get("/login-audit", response_model=list[LoginAuditResponse])
async def get_login_audit(
    user_id: int | None = Query(None, description="Filtrar por ID de usuario"),
    email: str | None = Query(None, description="Filtrar por email (búsqueda parcial)"),
    status: str | None = Query(None, description="Filtrar por status: SUCCESS, FAILED_INVALID_PASSWORD, FAILED_LOCKED, FAILED_USER_NOT_FOUND, FAILED_INACTIVE"),
    from_date: datetime | None = Query(None, description="Desde fecha (ISO 8601)"),
    to_date: datetime | None = Query(None, description="Hasta fecha (ISO 8601)"),
    limit: int = Query(100, ge=1, le=500, description="Máximo de registros"),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_db)
):
    """Consulta la bitácora de logins (solo SuperAdmin)."""
    if scope.role_code != "superadmin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    stmt = select(LoginAudit).order_by(LoginAudit.created_at.desc())
    
    if user_id:
        stmt = stmt.where(LoginAudit.user_id == user_id)
    if email:
        stmt = stmt.where(LoginAudit.email_attempted.ilike(f"%{email}%"))
    if status:
        stmt = stmt.where(LoginAudit.status == status)
    if from_date:
        stmt = stmt.where(LoginAudit.created_at >= from_date)
    if to_date:
        stmt = stmt.where(LoginAudit.created_at <= to_date)
    
    stmt = stmt.limit(limit)
    
    result = await db.execute(stmt)
    audits = result.scalars().all()
    
    return [LoginAuditResponse.model_validate(a) for a in audits]



@router.get("/login-audit/stats", response_model=LoginAuditStats)
async def get_login_audit_stats(
    days: int = Query(7, ge=1, le=90, description="Días hacia atrás para calcular estadísticas"),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_db)
):
    """Estadísticas agregadas de la bitácora de logins (solo SuperAdmin)."""
    if scope.role_code != "superadmin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    since = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Totales por status
    total = await db.scalar(
        select(func.count(LoginAudit.id)).where(LoginAudit.created_at >= since)
    ) or 0
    
    successful = await db.scalar(
        select(func.count(LoginAudit.id)).where(
            LoginAudit.created_at >= since,
            LoginAudit.status == "SUCCESS"
        )
    ) or 0
    
    failed = await db.scalar(
        select(func.count(LoginAudit.id)).where(
            LoginAudit.created_at >= since,
            LoginAudit.status.in_(["FAILED_INVALID_PASSWORD", "FAILED_USER_NOT_FOUND"])
        )
    ) or 0
    
    locked = await db.scalar(
        select(func.count(LoginAudit.id)).where(
            LoginAudit.created_at >= since,
            LoginAudit.status == "FAILED_LOCKED"
        )
    ) or 0
    
    # Usuarios únicos
    unique_users = await db.scalar(
        select(func.count(func.distinct(LoginAudit.user_id))).where(
            LoginAudit.created_at >= since,
            LoginAudit.user_id.isnot(None)
        )
    ) or 0
    
    # IPs únicas
    unique_ips = await db.scalar(
        select(func.count(func.distinct(LoginAudit.ip_address))).where(
            LoginAudit.created_at >= since,
            LoginAudit.ip_address.isnot(None)
        )
    ) or 0
    
    # Top 5 emails con más fallos
    top_failed_query = await db.execute(
        select(
            LoginAudit.email_attempted,
            func.count(LoginAudit.id).label("count")
        )
        .where(
            LoginAudit.created_at >= since,
            LoginAudit.status != "SUCCESS"
        )
        .group_by(LoginAudit.email_attempted)
        .order_by(func.count(LoginAudit.id).desc())
        .limit(5)
    )
    most_failed_emails = [
        {"email": row.email_attempted, "count": row.count}
        for row in top_failed_query.all()
    ]
    
    return LoginAuditStats(
        total_logins=total,
        successful=successful,
        failed=failed,
        locked=locked,
        unique_users=unique_users,
        unique_ips=unique_ips,
        most_failed_emails=most_failed_emails,
        hourly_distribution=[]  # Por simplicidad, no implementamos distribución horaria
    )

@router.post("/first-login-change-password", status_code=status.HTTP_200_OK)
async def first_login_change_password(
    payload: FirstLoginChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cambia la contraseña en el primer inicio de sesión.
    NO requiere la contraseña actual, pero valida la fortaleza de la nueva.
    """
    # 1. Validar fortaleza de la nueva contraseña
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

    # 2. Actualizar contraseña y limpiar estados
    current_user.hashed_password = get_password_hash(payload.new_password)
    current_user.must_change_password = False  # ✅ Ya cumplió el requisito
    current_user.is_locked = False
    current_user.locked_until = None
    current_user.failed_login_attempts = 0
    current_user.password_changed_at = datetime.now(timezone.utc)
    current_user.password_expires_at = calculate_password_expiration(days=90)
    
    await db.commit()
    
    logger.info(f"✅ Usuario {current_user.email} completó el cambio de contraseña del primer login")
    
    return {
        "message": "Contraseña actualizada exitosamente. Ya puedes usar el sistema.",
        "password_expires_at": current_user.password_expires_at.isoformat(),
    }