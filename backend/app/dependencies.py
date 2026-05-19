from fastapi import Depends, HTTPException, status
from app.db.session import get_tenant_db, oauth2_scheme
from sqlalchemy.ext.asyncio import AsyncSession

async def get_current_user(
    db: AsyncSession = Depends(get_tenant_db)
) -> dict:
    """
    Retorna el payload del JWT (que incluye user_id, tenant_id, schema, role).
    También se puede obtener directamente de db.info['current_user'].
    """
    return db.info.get("current_user")