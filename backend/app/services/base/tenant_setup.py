# app/services/tenant_setup.py
import logging
import os
import re
from pathlib import Path

import alembic.command
import alembic.config
from app.config import settings
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

# Schemas reservados que NUNCA deben migrarse
RESERVED_SCHEMAS = {"public", "system", "sistema", "information_schema", "pg_catalog"}


def validate_schema_name(schema_name: str) -> None:
    """
    Valida que el nombre del schema sea seguro y no reservado.
    
    Reglas:
    - No puede estar en RESERVED_SCHEMAS
    - Debe empezar con letra minúscula
    - Solo puede contener letras minúsculas, números y guiones bajos
    - Máximo 63 caracteres (límite PostgreSQL)
    """
    if not schema_name:
        raise ValueError("El nombre del schema no puede estar vacío")
    
    if schema_name.lower() in RESERVED_SCHEMAS:
        raise ValueError(
            f"El schema '{schema_name}' está reservado y no puede usarse como tenant"
        )
    
    if not re.match(r'^[a-z][a-z0-9_]*$', schema_name):
        raise ValueError(
            f"Schema inválido: '{schema_name}'. "
            "Debe empezar con letra minúscula y contener solo letras, números y guiones bajos."
        )
    
    if len(schema_name) > 63:
        raise ValueError(
            f"Schema inválido: '{schema_name}' excede el límite de 63 caracteres"
        )


def initialize_tenant_schema(
    schema_name: str,
    alembic_ini_name: str = "alembic_tenant.ini"
) -> None:
    """
    Crea el esquema PostgreSQL, otorga permisos y ejecuta TODAS las migraciones
    de alembic_tenant en orden cronológico.
    
    ⚠️ SÍNCRONA: Debe llamarse vía asyncio.to_thread() desde FastAPI.
    
    Args:
        schema_name: Nombre del schema (formato: t_<uuid_sin_guiones>)
        alembic_ini_name: Nombre del archivo de configuración de Alembic
    
    Raises:
        ValueError: Si el schema_name es inválido o reservado
        RuntimeError: Si falla la creación del schema o las migraciones
    """
    # 1. Validar nombre del schema
    validate_schema_name(schema_name)
    
    logger.info(f"🚀 Iniciando creación del schema '{schema_name}'")
    
    # 2. Crear schema y otorgar permisos
    _create_schema_with_privileges(schema_name)
    
    # 3. Ejecutar TODAS las migraciones en orden cronológico
    try:
        _run_alembic_upgrade(schema_name, alembic_ini_name)
        logger.info(f"✅ Schema '{schema_name}' creado y migrado exitosamente")
    except Exception as e:
        logger.error(f"❌ Error en migraciones de '{schema_name}': {e}")
        # Rollback automático: eliminar el schema parcialmente creado
        cleanup_tenant_schema(schema_name)
        raise RuntimeError(f"Error al migrar schema '{schema_name}': {e}") from e


def _create_schema_with_privileges(schema_name: str) -> None:
    """Crea el schema y otorga permisos necesarios."""
    engine = create_engine(settings.SYNC_DATABASE_URL, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conn:
            # Crear schema
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
            logger.debug(f"Schema '{schema_name}' creado")
            
            # Otorgar permisos al rol de la app
            db_user = settings.DATABASE_USER
            conn.execute(text(f'GRANT ALL ON SCHEMA "{schema_name}" TO "{db_user}"'))
            
            # Permisos automáticos para tablas/sequences creadas en el futuro
            conn.execute(text(
                f'ALTER DEFAULT PRIVILEGES IN SCHEMA "{schema_name}" '
                f'GRANT ALL ON TABLES TO "{db_user}"'
            ))
            conn.execute(text(
                f'ALTER DEFAULT PRIVILEGES IN SCHEMA "{schema_name}" '
                f'GRANT ALL ON SEQUENCES TO "{db_user}"'
            ))
            logger.debug(f"Permisos otorgados en '{schema_name}'")
    except Exception as e:
        raise RuntimeError(f"Error al crear esquema '{schema_name}': {e}") from e
    finally:
        engine.dispose()


def _run_alembic_upgrade(schema_name: str, alembic_ini_name: str) -> None:
    """
    Ejecuta `alembic upgrade head` usando la rama de tenants.
    
    ⭐ CRÍTICO: Inyecta TENANT_SCHEMA (no TARGET_SCHEMA) para que env.py lo lea.
    
    Alembic ejecutará TODAS las migraciones en orden cronológico:
    - Si el tenant es nuevo (sin tabla alembic_version), ejecuta desde la primera
    - Si ya tiene migraciones aplicadas, ejecuta solo las pendientes
    """
    # Ruta al archivo alembic_tenant.ini
    # app/services/tenant_setup.py -> raíz del proyecto -> alembic_tenant.ini
    alembic_ini_path = Path(__file__).resolve().parent.parent.parent.parent / alembic_ini_name
    
    if not alembic_ini_path.exists():
        raise FileNotFoundError(
            f"Configuración de Alembic no encontrada: {alembic_ini_path}"
        )
    
    config = alembic.config.Config(str(alembic_ini_path))
    
    # ⭐ CRÍTICO: Usar TENANT_SCHEMA (coincide con env.py de alembic_tenant)
    os.environ["TENANT_SCHEMA"] = schema_name
    
    try:
        logger.info(f"Ejecutando migraciones Alembic para schema '{schema_name}'")
        alembic.command.upgrade(config, "head")
    finally:
        # Limpiar la variable de entorno para no afectar otras operaciones
        if "TENANT_SCHEMA" in os.environ:
            del os.environ["TENANT_SCHEMA"]


def cleanup_tenant_schema(schema_name: str) -> None:
    """
    Elimina esquema y contenido. Para rollbacks de seguridad.
    
    ⚠️ NUNCA elimina schemas reservados (public, system, etc.)
    """
    # Protección adicional: nunca eliminar schemas reservados
    if schema_name.lower() in RESERVED_SCHEMAS:
        logger.warning(
            f"⚠️ Intento de eliminar schema reservado '{schema_name}'. "
            "Operación bloqueada."
        )
        return
    
    logger.info(f"🗑️ Eliminando schema '{schema_name}'")
    
    engine = create_engine(settings.SYNC_DATABASE_URL, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conn:
            conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
            logger.info(f"Schema '{schema_name}' eliminado")
    except Exception as e:
        logger.error(f"Error al eliminar schema '{schema_name}': {e}")
        raise RuntimeError(f"Error al eliminar schema '{schema_name}': {e}") from e
    finally:
        engine.dispose()