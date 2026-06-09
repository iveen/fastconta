# app/core/tenant_utils.py
import re

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import DataScope


async def set_tenant_search_path(db: AsyncSession, scope: DataScope, tenant_id: str | None = None) -> str:
    """Configura el search_path de forma segura y centralizada."""
    target_tenant_id = tenant_id if scope.role_code == "superadmin" else str(scope.tenant_id)
    
    if scope.role_code == "superadmin" and not tenant_id:
        raise HTTPException(400, detail="Superadmin debe especificar un tenant_id")

    res = await db.execute(
        text("SELECT schema_name FROM public.tenants WHERE id = :tid"), 
        {"tid": target_tenant_id}
    )
    row = res.first()
    if not row:
        raise HTTPException(404, detail="Tenant no encontrado")
    
    schema_name = row[0]
    
    # Validación más robusta contra inyección SQL que .replace().isalnum()
    if not re.match(r"^[a-zA-Z0-9_]+$", schema_name):
        raise HTTPException(500, detail="Schema con formato inválido o peligroso")

    # SET LOCAL es perfecto porque solo dura lo que dura la transacción/request
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    return schema_name