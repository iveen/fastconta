# alembic_tenant/env.py
import os
import sys
from logging.config import fileConfig
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from alembic import context
from app.config import settings
from app.db.base import Base
from sqlalchemy import engine_from_config, pool, text

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


config.set_main_option("sqlalchemy.url", settings.SYNC_DATABASE_URL)

# Importar SOLO modelos de tenant
from app.models.tenant_models import Empresa, CuentaContable, Partida, DetallePartida, Secuencia, PeriodoFiscal, FacturaElectronica, FacturaDetalle  # noqa

target_metadata = Base.metadata

def get_tenant_schema():
    return os.environ.get("TENANT_SCHEMA", "public")

def is_system_tenant():
    """Verifica si estamos migrando el tenant 'system' (inmutable)."""
    return get_tenant_schema() == "system"

def include_object(object, name, type_, reflected, compare_to):
    tenant_schema = get_tenant_schema()
    
    # Si estamos en modo autogenerate sin TENANT_SCHEMA setado, procesar todo (para debug)
    if not os.environ.get("TENANT_SCHEMA"):
        return True
        
    obj_schema = None
    
    if type_ == "table" and name == "alembic_version":
        return False

    if type_ == "table":
        obj_schema = getattr(object, 'schema', None)
    elif type_ == "column":
        tbl = getattr(object, 'table', None)
        # ¡CORRECCIÓN AQUÍ!: Cambiar 'if tbl' por 'if tbl is not None'
        obj_schema = getattr(tbl, 'schema', None) if tbl is not None else None
    elif type_ == "index" or type_ == "unique_constraint":
        tbl = getattr(object, 'table', None)
        # Asegurar 'is not None' también aquí por seguridad
        obj_schema = getattr(tbl, 'schema', None) if tbl is not None else None
    elif type_ == "foreign_key_constraint":
        tbl = getattr(object, 'table', None)
        obj_schema = getattr(tbl, 'schema', None) if tbl is not None else None

    # Lógica estricta:
    # 1. Si el objeto tiene schema explícito, debe coincidir con el tenant actual.
    # 2. Si el objeto NO tiene schema (None), lo aceptamos porque heredará el search_path del tenant.
    # 3. Rechazamos explícitamente schema 'public' u otros tenants.
    if obj_schema is not None and obj_schema != tenant_schema:
        return False
    
    return True

def run_migrations_offline():
    if is_system_tenant():
        return  # No migrar el tenant 'system' en modo offline
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
    if is_system_tenant():
        return  # No migrar el tenant 'system' en modo online
    # Asegurar que se asigne la URL dinámica antes de levantar el engine
    config.set_main_option("sqlalchemy.url", settings.SYNC_DATABASE_URL)

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    
    tenant_schema = get_tenant_schema()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            version_table="alembic_version",
            version_table_schema=tenant_schema,
            default_schema=tenant_schema,
            render_as_batch=True, 
        )

        with context.begin_transaction():
            # SOLUCIÓN: Ejecutar el search_path DENTRO de la transacción controlada por Alembic
            safe_schema = tenant_schema.replace('"', '""')
            connection.execute(text(f'SET search_path TO "{safe_schema}", public'))
            
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()