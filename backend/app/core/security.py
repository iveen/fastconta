# app/core/security.py
import re
import secrets
import string
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Set

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from passlib.context import CryptContext
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.jwt_utils import decode_access_token
from app.db.session import get_db
from app.models.global_models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Constantes de política
MAX_LOGIN_ATTEMPTS = 5
LOCK_DURATION_MINUTES = 15
PASSWORD_EXPIRATION_DAYS = 90

# Password Reset Token
token_hash_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

RESET_TOKEN_LENGTH = 64
RESET_TOKEN_EXPIRATION_MINUTES = 5

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    if len(password.encode()) > 72:
        raise ValueError("Password demasiado larga para bcrypt")
    return pwd_context.hash(password)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o expiradas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        if not payload or not payload.get("sub"):
            raise credentials_exception
        user_id = payload["sub"]
    except JWTError:
        raise credentials_exception

    try:
        user_id = int(payload.get("sub"))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token con formato inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    stmt = select(User).where(User.id == user_id).options(selectinload(User.tenant))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise credentials_exception
    return user

@dataclass
class DataScope:
    user: User
    role_code: str
    nivel_acceso: int
    tenant_id: int | None = None
    tenant_schema: str | None = None
    empresa_ids: Set[int] | None = field(default=None)
    is_read_only: bool = False

async def get_data_scope(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> DataScope:
    # 🔹 Extraer role_code de forma tolerante: puede ser string, objeto Role, o None
    role_value = getattr(current_user, 'role', 'tenant_member')
    is_read_only = False
    
    if role_value is None:
        role_code = 'tenant_member'
    elif isinstance(role_value, str):
        role_code = role_value.lower()
    elif hasattr(role_value, 'codigo'):  # Objeto Role con atributo 'codigo'
        role_code = str(role_value.codigo).lower()
    elif hasattr(role_value, 'name'):  # Objeto Role con atributo 'name'
        role_code = str(role_value.name).lower()
    elif hasattr(role_value, 'role'):  # Anidación extraña
        role_code = str(role_value.role).lower()
    else:
        # Fallback: convertir a string y limpiar representación de objeto
        role_str = str(role_value).lower()
        if 'object at 0x' in role_str:
            role_code = 'tenant_member'  # Fallback seguro
        else:
            role_code = role_str
    
    # Mapeo de niveles de acceso
    ROLE_LEVELS = {
        "superadmin": (100, False), "admin": (80, False), "tenant_manager": (80, False),
        "tenant_member": (60, False), "contador": (60, False), "auxiliar": (40, False),
        "tenant_client": (20, True), "cliente": (20, True),
    }
    nivel_acceso, is_read_only = ROLE_LEVELS.get(role_code, (0, True))
    
    scope = DataScope(
        user=current_user,
        role_code=role_code,
        nivel_acceso=nivel_acceso,
        is_read_only=is_read_only
    )

    if role_code == "superadmin":
        return scope

    if not current_user.tenant:
        raise HTTPException(403, "Usuario sin tenant asociado")

    scope.tenant_id = current_user.tenant.id
    scope.tenant_schema = current_user.tenant.schema_name
    await db.execute(text(f"SET LOCAL search_path TO {scope.tenant_schema}, public"))
    scope.empresa_ids = None
    return scope

def require_role(*allowed_roles: str):
    def checker(scope: DataScope = Depends(get_data_scope)):
        if scope.role_code not in [r.lower() for r in allowed_roles]:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"Acceso denegado. Roles permitidos: {', '.join(allowed_roles)}")
        return scope
    return checker

def require_write_access(scope: DataScope = Depends(get_data_scope)):
    if scope.is_read_only:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Acceso denegado: tu rol es de solo visualización.")
    return scope

#================================================================
# Funciones Relativas a Contraseñas
#================================================================

def generate_secure_password(length: int = 16) -> str:
    """
    Genera una contraseña segura con:
    - Mínimo 1 mayúscula
    - Mínimo 1 minúscula
    - Mínimo 1 número
    - Mínimo 1 símbolo
    - Longitud configurable (default 16)
    """
    if length < 12:
        raise ValueError("La longitud mínima es 12 caracteres")
    
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    
    # Asegurar al menos uno de cada tipo
    password = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*"),
    ]
    
    # Completar con caracteres aleatorios
    password += [secrets.choice(alphabet) for _ in range(length - 4)]
    
    # Mezclar
    secrets.SystemRandom().shuffle(password)
    
    return ''.join(password)


def calculate_password_expiration(days: int = PASSWORD_EXPIRATION_DAYS) -> datetime:
    """Calcula la fecha de expiración de la contraseña."""
    return datetime.now(timezone.utc) + timedelta(days=days)


def is_password_expired(user) -> bool:
    """Verifica si la contraseña del usuario ha expirado."""
    if not user.password_expires_at:
        return False
    return datetime.now(timezone.utc) > user.password_expires_at

def is_lock_expired(user) -> bool:
    """
    Verifica si el bloqueo del usuario EXPIRÓ (pero is_locked aún está en True).
    Útil para saber si hay que resetear el contador.
    """
    return (
        user.is_locked 
        and user.locked_until is not None 
        and datetime.now(timezone.utc) > user.locked_until
    )

def reset_expired_lock(user) -> None:
    """
    Resetea el estado de bloqueo si este ya expiró.
    Se llama al inicio del login para dar 5 intentos NUEVOS.
    """
    if is_lock_expired(user):
        user.failed_login_attempts = 0
        user.is_locked = False
        user.locked_until = None


def is_user_locked(user) -> bool:
    """
    Verifica si el usuario está bloqueado ACTUALMENTE.
    Retorna True solo si:
    - is_locked es True Y locked_until AÚN no ha pasado
    """
    if not user.is_locked:
        return False
    
    # Si el bloqueo ya expiró, NO está bloqueado actualmente
    if user.locked_until and datetime.now(timezone.utc) > user.locked_until:
        return False
    
    return True


def get_lock_remaining_minutes(user) -> int:
    """Retorna los minutos restantes de bloqueo."""
    if not user.locked_until:
        return 0
    remaining = (user.locked_until - datetime.now(timezone.utc)).total_seconds() / 60
    return max(0, int(remaining) + 1)


def register_failed_attempt(user) -> None:
    """Registra un intento fallido y bloquea si alcanza el límite."""
    user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
    
    if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
        user.is_locked = True
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCK_DURATION_MINUTES)
        user.must_change_password = True  # Forzar cambio al desbloquearse


def clear_failed_attempts(user) -> None:
    """
    Limpia completamente el estado de bloqueo tras un login exitoso.
    Se llama cuando el usuario inicia sesión correctamente.
    """
    user.failed_login_attempts = 0
    user.is_locked = False  # ✅ AHORA SÍ se limpia
    user.locked_until = None

# Lista de contraseñas más comunes (top 20 global)
COMMON_PASSWORDS = {
    "password", "123456", "12345678", "qwerty", "abc123", "monkey", "1234567",
    "letmein", "trustno1", "dragon", "baseball", "iloveyou", "master", "sunshine",
    "ashley", "bailey", "passw0rd", "shadow", "123123", "654321", "superman",
    "qazwsx", "michael", "football", "password1", "password123", "admin", "admin123",
    "root", "toor", "pass", "test", "guest", "master123", "changeme", "hello",
    "charlie", "donald", "password1!", "qwerty123", "1q2w3e4r", "1qaz2wsx",
}


def validate_password_strength(
    password: str,
    user_email: str | None = None,
    min_length: int = 12,
    max_length: int = 72,
) -> List[str]:
    """
    Valida la fortaleza de una contraseña.
    
    Args:
        password: Contraseña a validar
        user_email: Email del usuario (para verificar que no esté incluido)
        min_length: Longitud mínima (default 12)
        max_length: Longitud máxima (default 72, límite de bcrypt)
    
    Returns:
        Lista de errores. Vacía si la contraseña es válida.
    """
    errors = []
    
    # 1. Validar longitud
    if len(password) < min_length:
        errors.append(f"La contraseña debe tener al menos {min_length} caracteres")
    
    if len(password) > max_length:
        errors.append(f"La contraseña no puede tener más de {max_length} caracteres")
    
    # 2. Validar complejidad
    if not re.search(r'[A-Z]', password):
        errors.append("Debe contener al menos una letra mayúscula")
    
    if not re.search(r'[a-z]', password):
        errors.append("Debe contener al menos una letra minúscula")
    
    if not re.search(r'\d', password):
        errors.append("Debe contener al menos un número")
    
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        errors.append("Debe contener al menos un símbolo (!@#$%^&*)")
    
    # 3. Validar que no sea una contraseña común
    if password.lower() in COMMON_PASSWORDS:
        errors.append("Esta contraseña es demasiado común y no es segura")
    
    # 4. Validar que no contenga el email del usuario
    if user_email:
        email_prefix = user_email.split('@')[0].lower()
        if email_prefix in password.lower():
            errors.append("La contraseña no puede contener tu email")
        
        # Validar dominios comunes
        for domain in ['fastconta', 'gmail', 'hotmail', 'yahoo']:
            if domain in password.lower():
                errors.append(f"La contraseña no puede contener '{domain}'")
    
    # 5. Validar que no tenga caracteres repetidos excesivos
    if re.search(r'(.)\1{3,}', password):
        errors.append("No puede tener 4 o más caracteres repetidos consecutivos")
    
    # 6. Validar que no sea una secuencia obvia
    obvious_sequences = ['1234', 'abcd', 'qwerty', 'asdf', 'zxcv']
    for seq in obvious_sequences:
        if seq in password.lower():
            errors.append(f"No puede contener la secuencia '{seq}'")
            break
    
    return errors


def is_password_strong(password: str, user_email: str | None = None) -> bool:
    """
    Verifica si una contraseña es segura.
    
    Returns:
        True si la contraseña cumple todos los requisitos
    """
    return len(validate_password_strength(password, user_email)) == 0

#========================================================================
# Password Reset Token Functions
#========================================================================
def generate_reset_token() -> tuple[str, str]:
    """Retorna (token_plano, token_hash)"""
    plain = secrets.token_urlsafe(RESET_TOKEN_LENGTH)
    return plain, token_hash_ctx.hash(plain)

def verify_reset_token(plain: str, token_hash: str) -> bool:
    return token_hash_ctx.verify(plain, token_hash)
