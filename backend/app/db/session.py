from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text                        # <-- Añadir import
from app.db.base import AsyncSessionLocal
from app.core.security import decode_access_token
from fastapi.security import OAuth2PasswordBearer
from app.core.tenant import tenant_schema_exists

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

async def get_tenant_db(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> AsyncSession:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )
    schema_name = payload.get("schema")
    if not schema_name:
        raise HTTPException(status_code=400, detail="Token sin schema de tenant")

    # Verificar que el schema exista
    if not await tenant_schema_exists(db, schema_name):
        raise HTTPException(status_code=400, detail="El tenant asociado al token no está configurado correctamente")

    # Envolver con text()
    await db.execute(text(f"SET search_path TO {schema_name}, public"))
    db.info["current_user"] = payload
    return db