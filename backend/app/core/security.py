from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Configuración de autenticación
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta
        if expires_delta
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_password_hash(password: str) -> str:
    print(f"Password length: {len(password)} bytes: {len(password.encode())}")
    if len(password.encode()) > 72:
        raise ValueError("Password demasiado larga para bcrypt")
    return pwd_context.hash(password)


# ==========================================
# DEPENDENCIAS DE AUTENTICACIÓN
# ==========================================


async def get_current_active_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends()
) -> dict:
    """Valida JWT y retorna usuario activo. Base para todas las rutas protegidas."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o expiradas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(
        text(
            "SELECT id, email, full_name, role, tenant_id, is_active FROM public.users WHERE id = :uid"
        ),
        {"uid": user_id},
    )
    user = result.mappings().first()

    if not user or not user["is_active"]:
        raise credentials_exception

    return dict(user)


async def get_current_superadmin(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(),
) -> dict:
    """
    Envuelve get_current_active_user y valida que el rol sea 'superadmin'.
    Úsala en endpoints que solo el dueño de la plataforma debe acceder.
    """
    if current_user["role"] != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requieren permisos de Superadministrador.",
        )
    return current_user


# core/dependencies.py
async def get_current_tenant_user(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(),
):
    """Valida que el usuario tenga tenant_id y configura search_path."""
    if not current_user.get("tenant_id"):
        raise HTTPException(403, "Acceso denegado: usuario sin tenant asociado")

    # Configurar search_path para este request
    schema = current_user.get("schema")  # Viene del token
    if schema:
        await db.execute(text(f"SET search_path TO {schema}, public"))

    return current_user
