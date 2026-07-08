# app/core/jwt_utils.py
from datetime import datetime, timedelta

from jose import jwt

from app.config import settings


def create_access_token(
    user_id: int,           # ✅ Debe ser int, no str
    tenant_id: int,         # ✅ Debe ser int, no str
    email: str,
    role: str,
    schema: str,
    tenant_name: str,
    expires_delta: timedelta | None = None
) -> str:
    """
    Crea un JWT token con los datos del usuario.
    
    ⚠️ IMPORTANTE: user_id y tenant_id deben ser int, no str.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "sub": str(user_id),          # JWT requiere string en "sub"
        "user_id": user_id,           # ✅ NUEVO: Guardar como int también
        "tenant_id": tenant_id,       # ✅ int (no string)
        "email": email,
        "role": role,
        "schema": schema,
        "tenant_name": tenant_name,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decodifica un JWT token y retorna el payload.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None