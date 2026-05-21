from fastapi import Depends, HTTPException, status
from app.db.session import get_tenant_db, oauth2_scheme
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_access_token

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return payload

def require_role(*allowed_roles: str):
    """Factory que retorna una dependencia que valida que el usuario tenga uno de los roles permitidos."""
    async def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Permisos insuficientes")
        return current_user
    return role_checker