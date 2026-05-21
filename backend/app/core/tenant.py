import os
import asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from alembic.config import Config
from alembic import command

ALEMBIC_TENANT_INI = str(Path(__file__).parent.parent.parent / "alembic_tenant.ini")

async def tenant_schema_exists(db: AsyncSession, schema_name: str) -> bool:
    query = text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = :schema")
    result = await db.execute(query, {"schema": schema_name})
    return result.scalar_one_or_none() is not None

async def create_tenant_schema(db: AsyncSession, schema_name: str) -> None:

    SCRIPT_PATH = Path(__file__).parent.parent.parent / "db" / "create_tenant_tables.sql"
    # 1. Crear schema
    await db.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
    # 2. Otorgar permisos
    await db.execute(text(f"GRANT ALL ON SCHEMA {schema_name} TO fastconta_user"))
    await db.execute(text(f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema_name} GRANT ALL ON TABLES TO fastconta_user"))
    await db.execute(text(f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema_name} GRANT ALL ON SEQUENCES TO fastconta_user"))
    await db.commit()

    # 3. Leer el script y reemplazar el placeholder
    with open(SCRIPT_PATH, "r") as f:
        sql_template = f.read()
    sql = sql_template.replace("{schema}", schema_name)

    # 4. Ejecutar cada sentencia individualmente
    for statement in sql.split(";"):
        if statement.strip():
            await db.execute(text(statement))
    await db.commit()

    # 5. Aplicar todas las migraciones de tenant en el nuevo schema
    await db.execute(text(f"""
    DO $$
    DECLARE r RECORD;
    BEGIN
    FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = '{schema_name}'
    LOOP
        EXECUTE 'ALTER TABLE {schema_name}.' || r.tablename || ' OWNER TO fastconta_user';
    END LOOP;
    FOR r IN SELECT sequencename FROM pg_sequences WHERE schemaname = '{schema_name}'
    LOOP
        EXECUTE 'ALTER SEQUENCE {schema_name}.' || r.sequencename || ' OWNER TO fastconta_user';
    END LOOP;
    END $$;
    """))
    await db.commit()
    os.environ["TENANT_SCHEMA"] = schema_name
    alembic_cfg = Config(ALEMBIC_TENANT_INI)
    alembic_cfg.set_main_option("script_location", "alembic_tenant")
    await asyncio.to_thread(command.upgrade, alembic_cfg, "head")
    os.environ.pop("TENANT_SCHEMA", None)