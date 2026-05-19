from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

async def tenant_schema_exists(db: AsyncSession, schema_name: str) -> bool:
    """Verifica si un schema existe en la base de datos."""
    query = text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = :schema")
    result = await db.execute(query, {"schema": schema_name})
    return result.scalar_one_or_none() is not None

async def create_tenant_schema(db: AsyncSession, schema_name: str) -> None:
    """Crea el schema del tenant y sus tablas mínimas."""
    from sqlalchemy import text
    # 1. Crear schema y dar privilegios
    await db.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
    # Otorgar permisos sobre el schema al usuario de la aplicación
    await db.execute(text(f"GRANT ALL ON SCHEMA {schema_name} TO fastconta_user"))
    # Establecer privilegios predeterminados para tablas y secuencias
    await db.execute(text(f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema_name} GRANT ALL PRIVILEGES ON TABLES TO fastconta_user"))
    await db.execute(text(f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema_name} GRANT ALL PRIVILEGES ON SEQUENCES TO fastconta_user"))
    await db.commit()
    # 2. Establecer search_path temporal para crear las tablas dentro de él
    await db.execute(text(f"SET search_path TO {schema_name}"))
    # 3. Crear tabla de ejemplo: empresas
    await db.execute(text("""
        CREATE TABLE IF NOT EXISTS empresas (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            nombre VARCHAR(255) NOT NULL,
            nit VARCHAR(20) UNIQUE NOT NULL,
            direccion TEXT,
            created_at TIMESTAMPTZ DEFAULT now()
        )
    """))
    # 4. Restaurar search_path a public para no afectar otras operaciones
    await db.execute(text("SET search_path TO public"))