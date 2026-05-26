import os
import sys
from pathlib import Path
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, text
from alembic import context

# 🔹 RUTA CORREGIDA
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.config import settings
config.set_main_option("sqlalchemy.url", settings.SYNC_DATABASE_URL)

# Solo metadata de tenant
from app.db.base import Base
from app.models.tenant_models import Empresa, CuentaContable, Partida, DetallePartida, Secuencia, PeriodoFiscal, FacturaElectronica, FacturaDetalle  # noqa
target_metadata = Base.metadata

def include_object(object, name, type_, reflected, compare_to):
    tenant_schema = os.environ.get("TENANT_SCHEMA")
    
    # 🔹 Durante revision/autogenerate: NO filtrar. Alembic necesita ver toda la metadata para generar el diff.
    if not tenant_schema:
        return True
        
    # 🔹 Durante upgrade/downgrade: filtrar estrictamente por el schema activo
    obj_schema = None
    if type_ == "table":
        obj_schema = object.schema
    elif type_ == "column":
        obj_schema = object.table.schema if object.table is not None else None
    else:
        tbl = getattr(object, 'table', None)
        obj_schema = tbl.schema if tbl is not None else getattr(object, 'schema', None)
        
    return obj_schema == tenant_schema

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    tenant_schema = os.environ.get("TENANT_SCHEMA") or "public"
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        version_table_schema=tenant_schema,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    tenant_schema = os.environ.get("TENANT_SCHEMA")
    
    # Validación solo para upgrade/downgrade real
    is_upgrade = len(sys.argv) > 1 and sys.argv[1] in ("upgrade", "downgrade")
    if not tenant_schema and is_upgrade:
        raise RuntimeError("TENANT_SCHEMA no definida. Úsala así: TENANT_SCHEMA=tenant_xxx alembic upgrade head")
    
    if not tenant_schema:
        tenant_schema = "public"

    with connectable.connect() as connection:
        connection.execute(text(f"SET search_path TO {tenant_schema}, public"))
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            version_table_schema=tenant_schema,
            default_schema=tenant_schema,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()