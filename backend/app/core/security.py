# app/core/security.py
from dataclasses import dataclass, field
from typing import Set

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


