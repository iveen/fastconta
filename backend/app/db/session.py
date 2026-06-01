# backend/app/db/session.py

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text                
from app.db.base import AsyncSessionLocal
from app.core.security import decode_access_token
from fastapi.security import OAuth2PasswordBearer
from app.core.tenant import tenant_schema_exists
from typing import AsyncGenerator
import logging

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

async def get_public_db() -> AsyncGenerator[AsyncSession, None]:
    """Sesión para acceder exclusivamente al esquema public."""
    async with AsyncSessionLocal() as session:
        # Forzar search_path a public para evitar fugas a schemas de tenant
        await session.execute(text("SET search_path TO public"))
        try:
            yield session
        finally:
            await session.close()

async def get_tenant_db(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> AsyncSession:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    schema_name = payload.get("schema")
    if not schema_name:
        raise HTTPException(status_code=400, detail="Token sin schema")

    if not await tenant_schema_exists(db, schema_name):
        raise HTTPException(status_code=400, detail="Tenant no configurado")

    # 🔹 CRÍTICO: Asegurar que el SET se aplica en la conexión subyacente
    # Opción 1: Ejecutar y hacer flush para aplicar el cambio
    await db.execute(text(f"SET search_path TO {schema_name}, public"))
    await db.flush()  # ← Aplica el SET sin cerrar transacción
    
    
    # 🔹 Opción 2 (más robusta): Configurar a nivel de conexión raw
    # await db.sync_session.connection().execute(text(f"SET search_path TO {schema_name}, public"))
    
    # Debug temporal: imprime en consola (visible en terminal de uvicorn)
    result = await db.execute(text("SELECT current_schema()"))
    logger.info(f"Search path aplicado: schema={schema_name}")
    
    db.info["current_user"] = payload
    return db