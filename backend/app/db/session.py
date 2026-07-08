# app/db/session.py
import logging
from modulefinder import test
from typing import AsyncGenerator

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jwt_utils import decode_access_token
from app.core.tenant import tenant_schema_exists
from app.db.base import AsyncSessionLocal

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependencia base: garantiza cierre de sesión incluso con excepciones"""
    session = AsyncSessionLocal()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()  # 👈 CRÍTICO: siempre cerrar

async def get_public_db() -> AsyncGenerator[AsyncSession, None]:
    """Sesión forzada a schema public"""
    session = AsyncSessionLocal()
    try:
        await session.execute(text("SET SESSION search_path TO public"))
        yield session
    finally:
        await session.close()

async def get_tenant_db(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> AsyncSession:
    """Configura search_path dinámico para tenant"""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    schema_name = payload.get("schema")
    if not schema_name:
        raise HTTPException(status_code=400, detail="Token sin schema")
    
    if not await tenant_schema_exists(db, schema_name):
        raise HTTPException(status_code=400, detail="Tenant no configurado")
    
    # 👇 SET LOCAL: el cambio solo aplica a esta transacción, no al pool
    await db.execute(test("RESET LOCAL search_path"))
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    await db.flush()
    
    db.info["current_user"] = payload
    return db