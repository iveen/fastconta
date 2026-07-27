import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, event, pool, text

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

target_metadata = Base.metadata

def include_object(object, name, type_, reflected, compare_to):
    """Filtra objetos para que solo incluya tablas del schema public"""
    # Excluir explícitamente alembic_version del autogenerate
    if type_ == "table" and name == "alembic_version":
        return False
    
    # Obtener schema del objeto
    obj_schema = None
    if type_ == "table":
        obj_schema = getattr(object, 'schema', None)
    elif type_ == "column":
        obj_schema = object.table.schema if object.table is not None else None
    
    # Permitir solo: schema None (default) o schema 'public'
    # Rechazar: cualquier otro schema (tenants)
    return obj_schema is None or obj_schema == "public"

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        version_table="alembic_version",
        version_table_schema="public",  # ✅ CRÍTICO: Forzar schema public
        default_schema="public",
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    
    # ✅ Forzar search_path ANTES de cualquier operación
    @event.listens_for(connectable, "connect")
    def set_search_path(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("SET search_path TO public, pg_catalog")
        cursor.close()
    
    with connectable.connect() as connection:
        # ✅ Verificar que alembic_version existe en public
        connection.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'alembic_version'
                ) THEN
                    CREATE TABLE public.alembic_version (
                        version_num VARCHAR(32) NOT NULL,
                        CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                    );
                END IF;
            END $$;
        """))
        connection.commit()
        
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            version_table="alembic_version",
            version_table_schema="public",  # ✅ CRÍTICO
            default_schema="public",
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
