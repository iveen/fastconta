import os
import sys
from pathlib import Path

# 🔹 FIX CRÍTICO: __file__ (con guiones bajos) y .resolve() para rutas absolutas seguras
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.config import settings
from app.models.global_models import Tenant

ALEMBIC_GLOBAL_INI = str(BASE_DIR / "alembic.ini")
ALEMBIC_TENANT_INI = str(BASE_DIR / "alembic_tenant.ini")

def get_sync_session():
    engine = create_engine(settings.SYNC_DATABASE_URL, echo=False)
    return Session(engine)

def run_public_migrations():
    print("🌍 Aplicando migraciones GLOBALES (schema public)...")
    alembic_cfg = Config(ALEMBIC_GLOBAL_INI)
    alembic_cfg.set_main_option("script_location", "alembic")
    command.upgrade(alembic_cfg, "head")
    print("✅ Migraciones globales aplicadas correctamente.")

def run_tenant_migrations():
    print("🏢 Iniciando migraciones para TENANTS activos...")
    session = get_sync_session()
    try:
        tenants = session.execute(select(Tenant).where(Tenant.is_active == True)).scalars().all()
        
        if not tenants:
            print("⚠️ No se encontraron tenants activos. Abortando.")
            return

        # Creamos la configuración una sola vez (es thread-safe para este uso secuencial)
        alembic_cfg = Config(ALEMBIC_TENANT_INI)
        alembic_cfg.set_main_option("script_location", "alembic_tenant")
        
        for tenant in tenants:
            schema_name = tenant.schema_name
            print(f"🔹 Procesando tenant: {schema_name}...")
            
            # 🔑 CRÍTICO: Inyectar variable ANTES de llamar a Alembic
            os.environ["TENANT_SCHEMA"] = schema_name
            
            try:
                command.upgrade(alembic_cfg, "head")
                print(f"   ✅ {schema_name} actualizado exitosamente.")
            except Exception as e:
                print(f"   ❌ Error en {schema_name}: {e}")
                # ⚠️ Decide si prefieres detener todo o continuar con el siguiente tenant
                # raise 
            finally:
                #  Limpieza inmediata para evitar contaminación entre iteraciones
                os.environ.pop("TENANT_SCHEMA", None)
                
    finally:
        session.close()
        
    print("🎉 Proceso de migración de tenants finalizado.")

def run_tenant_migrations_stamp(target_revision: str = "head"):
    """Marca migraciones como aplicadas sin ejecutar SQL (útil para sincronizar estados tras parches manuales)"""
    print(f"🏷️ Sincronizando estado (stamp) para TENANTS a {target_revision}...")
    session = get_sync_session()
    try:
        tenants = session.execute(select(Tenant).where(Tenant.is_active == True)).scalars().all()
        
        alembic_cfg = Config(ALEMBIC_TENANT_INI)
        alembic_cfg.set_main_option("script_location", "alembic_tenant")
        
        for tenant in tenants:
            schema_name = tenant.schema_name
            print(f"🔹 Marcando {schema_name}...")
            
            os.environ["TENANT_SCHEMA"] = schema_name
            command.stamp(alembic_cfg, target_revision)
            print(f"   ✅ {schema_name} sincronizado.")
            os.environ.pop("TENANT_SCHEMA", None)
    finally:
        session.close()
        os.environ.pop("TENANT_SCHEMA", None)
        
    print("✅ Sincronización de stamps finalizada.")

# 🔹 FIX CRÍTICO: __name__ y __main__ (faltaban guiones bajos)
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Gestor de migraciones FastConta")
    # 🔹 FIX: Eliminar espacios trailing en choices que rompían argparse
    parser.add_argument(
        "command", 
        choices=["public", "tenants", "stamp-tenants", "all"],
        help="Comando a ejecutar: public, tenants, stamp-tenants, all"
    )
    args = parser.parse_args()
    
    if args.command == "public":
        run_public_migrations()
    elif args.command == "tenants":
        run_tenant_migrations()
    elif args.command == "stamp-tenants":
        run_tenant_migrations_stamp("head")
    elif args.command == "all":
        run_public_migrations()
        run_tenant_migrations()