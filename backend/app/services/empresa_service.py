# app/services/empresa_service.py
import logging
from uuid import UUID

from app.models.tenant_models import Empresa
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def get_empresa_by_id(db: AsyncSession, empresa_id: UUID) -> Empresa | None:
    """
    Obtiene una empresa por su ID.
    Requiere que el search_path ya esté configurado al schema correcto.
    """
    result = await db.execute(
        select(Empresa).where(Empresa.id == empresa_id)
    )
    return result.scalar_one_or_none()


async def list_empresas_activas(db: AsyncSession) -> list[Empresa]:
    """
    Lista todas las empresas activas del tenant actual.
    Requiere que el search_path ya esté configurado al schema correcto.
    """
    result = await db.execute(
        select(Empresa)
        .where(Empresa.is_active.is_(True))
        .order_by(Empresa.nombre)
    )
    return list(result.scalars().all())


async def list_all_empresas(db: AsyncSession) -> list[Empresa]:
    """
    Lista todas las empresas del tenant actual (incluyendo inactivas).
    Requiere que el search_path ya esté configurado al schema correcto.
    """
    result = await db.execute(
        select(Empresa).order_by(Empresa.nombre)
    )
    return list(result.scalars().all())


async def configure_search_path_for_tenant(
    db: AsyncSession, 
    tenant_id: UUID
) -> str:
    """
    Configura el search_path para un tenant específico.
    Retorna el schema_name configurado.
    Útil para superadmin que necesita cambiar de contexto.
    """
    result = await db.execute(
        text("SELECT schema_name FROM public.tenants WHERE id = :tid"),
        {"tid": str(tenant_id)}
    )
    row = result.first()
    
    if not row:
        raise ValueError(f"Tenant {tenant_id} no encontrado")
    
    schema_name = row[0]
    
    # Validación de seguridad
    if not schema_name.strip().replace("_", "").isalnum():
        raise ValueError("Esquema con formato inválido")
    
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    return schema_name