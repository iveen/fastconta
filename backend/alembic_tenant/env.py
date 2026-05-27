# alembic_tenant/env.py
import os
import sys
from pathlib import Path
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, event, text
from alembic import context

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.config import settings
config.set_main_option("sqlalchemy.url", settings.SYNC_DATABASE_URL)

# Importar SOLO modelos de tenant
from app.db.base import Base
from app.models.tenant_models import Empresa, CuentaContable, Partida, DetallePartida, Secuencia, PeriodoFiscal, FacturaElectronica, FacturaDetalle  # noqa

target_metadata = Base.metadata

def get_tenant_schema():
    return os.environ.get("TENANT_SCHEMA", "public")

def include_object(object, name, type_, reflected, compare_to):
    tenant_schema = get_tenant_schema()
    
    # Si estamos en modo autogenerate sin TENANT_SCHEMA setado, procesar todo (para debug)
    if not os.environ.get("TENANT_SCHEMA"):
        return True
        
    obj_schema = None
    if type_ == "table":
        obj_schema = getattr(object, 'schema', None)
    elif type_ == "column":
        tbl = getattr(object, 'table', None)
        obj_schema = getattr(tbl, 'schema', None) if tbl else None
    else:
        obj_schema = getattr(object, 'schema', None)

    # Lógica estricta:
    # 1. Si el objeto tiene schema explícito, debe coincidir con el tenant actual.
    # 2. Si el objeto NO tiene schema (None), lo aceptamos porque heredará el search_path del tenant.
    # 3. Rechazamos explícitamente schema 'public' u otros tenants.
    if obj_schema is not None and obj_schema != tenant_schema:
        return False
    
    return True

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    tenant_schema = get_tenant_schema()
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        version_table="alembic_version",
        version_table_schema=tenant_schema, # CRÍTICO: La tabla de version va dentro del schema
        default_schema=tenant_schema,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    
    tenant_schema = get_tenant_schema()

    # Configurar conexión específica para este tenant
    @event.listens_for(connectable, "connect")
    def set_search_path(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        # Usamos comillas dobles seguras por si el nombre tiene espacios o chars raros
        # Aunque lo ideal es naming convention simple (lowercase snake_case)
        safe_schema = tenant_schema.replace('"', '""') 
        cursor.execute(f'SET search_path TO "{safe_schema}", public')
        cursor.close()

    with connectable.connect() as connection:
        # Verificación extra de seguridad al inicio
        connection.execute(text(f'SET search_path TO "{tenant_schema}", public'))

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            version_table="alembic_version",
            version_table_schema=tenant_schema,
            default_schema=tenant_schema,
            # Compare type para evitar falsos positivos en tipos de DB
            render_as_batch=True, 
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()