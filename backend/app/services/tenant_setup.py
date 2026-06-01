import os

import alembic.command
import alembic.config
from app.config import settings  # Ajusta si tu import es diferente
from sqlalchemy import create_engine, text


def initialize_tenant_schema(schema_name: str, alembic_ini_name: str = "alembic_tenant.ini") -> None:
    """
    Crea el esquema PostgreSQL, otorga permisos y ejecuta migraciones.
    ⚠️ SÍNCRONA: Debe llamarse vía asyncio.to_thread()
    """
    engine = create_engine(settings.DATABASE_URL, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conn:
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
            # Otorga permisos al rol que usa la app
            conn.execute(text(f'GRANT ALL ON SCHEMA "{schema_name}" TO {settings.DB_USER}'))
            # Permisos automáticos para tablas creadas en el futuro
            conn.execute(text(f'ALTER DEFAULT PRIVILEGES IN SCHEMA "{schema_name}" GRANT ALL ON TABLES TO {settings.DB_USER}'))
    except Exception as e:
        raise RuntimeError(f"Error al crear esquema '{schema_name}': {e}")
    finally:
        engine.dispose()

    _run_alembic_upgrade(schema_name, alembic_ini_name)

def cleanup_tenant_schema(schema_name: str) -> None:
    """Elimina esquema y contenido. Para rollbacks de seguridad."""
    engine = create_engine(settings.DATABASE_URL, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conn:
            conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
    finally:
        engine.dispose()

def _run_alembic_upgrade(schema_name: str, alembic_ini_name: str) -> None:
    """Ejecuta `alembic upgrade head` usando tu rama de tenants."""
    # Ruta relativa: app/services/tenant_setup.py -> backend/alembic_tenant.ini
    alembic_ini_path = os.path.join(os.path.dirname(__file__), f"../{alembic_ini_name}")
    if not os.path.exists(alembic_ini_path):
        raise FileNotFoundError(f"Configuración de Alembic no encontrada: {alembic_ini_path}")

    config = alembic.config.Config(alembic_ini_path)
    
    # Inyecta el schema para que env.py lo lea
    os.environ["TARGET_SCHEMA"] = schema_name
    alembic.command.upgrade(config, "head")