# backend/app/db/session.py
import logging
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jwt_utils import decode_access_token
from app.db.base import AsyncSessionLocal

logger = logging.getLogger(__name__)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependencia base: garantiza cierre de sesión incluso con excepciones"""
    session = AsyncSessionLocal()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

async def get_public_db() -> AsyncGenerator[AsyncSession, None]:
    """Sesión forzada a schema public"""
    session = AsyncSessionLocal()
    try:
        await session.execute(text("SET SESSION search_path TO public"))
        yield session
    finally:
        await session.close()

async def get_tenant_db(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> AsyncGenerator[AsyncSession, None]:
    """
    Configura search_path dinámico para el tenant del usuario autenticado.
    Lee el token directamente de la cookie HttpOnly o del header Authorization,
    evitando así cualquier importación circular con app.core.security.
    """
    # 1. Extraer el token de la cookie HttpOnly (prioridad) o del header
    auth_cookie = request.cookies.get("access_token")
    token = None
    
    if auth_cookie and auth_cookie.startswith("Bearer "):
        token = auth_cookie[7:]
    else:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            
    if not token:
        raise HTTPException(
            status_code=401, 
            detail="No se proporcionó token de autenticación"
        )
        
    # 2. Decodificar el token para obtener el schema
    payload = decode_access_token(token)
    if not payload or not payload.get("schema"):
        raise HTTPException(
            status_code=401, 
            detail="Token inválido o sin esquema de tenant"
        )
        
    schema_name = payload.get("schema")
    
    # 3. Configurar search_path para esta transacción
    try:
        await db.execute(text("RESET search_path"))
        await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
        yield db
    finally:
        # Limpieza al final de la request (buena práctica)
        await db.execute(text("RESET search_path"))
