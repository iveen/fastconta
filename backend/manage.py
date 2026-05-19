import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.global_models import Tenant

ALEMBIC_GLOBAL_INI = str(Path(__file__).parent / "alembic.ini")
ALEMBIC_TENANT_INI = str(Path(__file__).parent / "alembic_tenant.ini")

def get_sync_session():
    engine = create_engine(settings.SYNC_DATABASE_URL, echo=False)
    return Session(engine)

def run_public_migrations():
    alembic_cfg = Config(ALEMBIC_GLOBAL_INI)
    alembic_cfg.set_main_option("script_location", "alembic")
    command.upgrade(alembic_cfg, "global")
    print("Migraciones globales aplicadas.")

def run_tenant_migrations():
    session = get_sync_session()
    try:
        tenants = session.execute(select(Tenant).where(Tenant.is_active == True)).scalars().all()
        if not tenants:
            print("No hay tenants activos.")
            return
        for tenant in tenants:
            schema_name = tenant.schema_name
            print(f"Aplicando migraciones de tenant a {schema_name}...")
            alembic_cfg = Config(ALEMBIC_TENANT_INI)   # <-- Usa exclusivamente la config de tenant
            alembic_cfg.set_main_option("script_location", "alembic_tenant")
            os.environ["TENANT_SCHEMA"] = schema_name
            command.upgrade(alembic_cfg, "head")
            os.environ.pop("TENANT_SCHEMA", None)
            print(f"Migraciones de tenant aplicadas a {schema_name}.")
    finally:
        session.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["public", "tenants", "all"])
    args = parser.parse_args()

    if args.command == "public":
        run_public_migrations()
    elif args.command == "tenants":
        run_tenant_migrations()
    elif args.command == "all":
        run_public_migrations()
        run_tenant_migrations()