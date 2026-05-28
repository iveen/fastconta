# alembic/env.py
import os
import sys
from pathlib import Path
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, event
from alembic import context

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.config import settings
config.set_main_option("sqlalchemy.url", settings.SYNC_DATABASE_URL)

# Importar SOLO modelos globales para evitar contaminación de metadata
from app.db.base import Base
from app.models.global_models import Tenant, User  # noqa

# Filtrar metadata para que solo contenga tablas de public
target_metadata = Base.metadata

def include_object(object, name, type_, reflected, compare_to):
    # En modo público, rechazamos explícitamente cualquier objeto que tenga un schema asignado
    # que NO sea 'public' o None.
    obj_schema = getattr(object, 'schema', None)

    # Ignorar alembic_version en migraciones, ésto es autogestionado por el mismo alembic
    if type_ == "table" and name == "alembic_version":
        return False
    
    if type_ == "table":
        obj_schema = object.schema
    elif type_ == "column":
        obj_schema = object.table.schema if object.table is not None else None
    
    # Permitir: schema None (default) o schema 'public'
    # Rechazar: cualquier otro schema (tenants)
    return obj_schema is None or obj_schema == "public"

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        version_table="alembic_version", # Tabla en public por defecto
        version_table_schema="public",
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    # Forzar search_path limpio para público
    @event.listens_for(connectable, "connect")
    def set_search_path(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("SET search_path TO public, pg_catalog")
        cursor.close()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            version_table="alembic_version",
            version_table_schema="public",
            default_schema="public",
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()