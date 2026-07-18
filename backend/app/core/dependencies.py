"""
Dependencias auxiliares para endpoints.
Complementa app.core.security con helpers específicos de dominio.
"""
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def resolve_public_id(
    db: AsyncSession,
    model: Any,
    public_id: UUID,
    tenant_id: int,
    error_msg: str = "Registro no encontrado",
) -> Any:
    """
    Resuelve un public_id (UUID) a un registro ORM, validando tenant.

    Uso:
        empresa = await resolve_public_id(db, Empresa, empresa_public_id, scope.tenant_id)

    Nota: Se usa `Any` en lugar de `type[Base]` porque `Base` es una instancia
    de `DeclarativeMeta`, no una clase, lo que causa error en Pylance.
    """
    stmt = (
        select(model)
        .where(
            model.public_id == public_id,
            model.tenant_id == tenant_id,
        )
    )
    result = await db.execute(stmt)
    registro = result.scalar_one_or_none()

    if not registro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_msg,
        )
    return registro


async def resolve_public_id_global(
    db: AsyncSession,
    model: Any,
    public_id: UUID,
    error_msg: str = "Registro no encontrado",
) -> Any:
    """
    Resuelve un public_id sin validar tenant (para modelos globales como Tenant, User).
    """
    stmt = select(model).where(model.public_id == public_id)
    result = await db.execute(stmt)
    registro = result.scalar_one_or_none()

    if not registro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_msg,
        )
    return registro