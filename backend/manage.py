# backend/manage.py
import os
import sys
from pathlib import Path
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, select, text, inspect
from sqlalchemy.orm import Session
from app.config import settings
from app.models.global_models import Tenant

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

ALEMBIC_GLOBAL_INI = str(BASE_DIR / "alembic.ini")
ALEMBIC_TENANT_INI = str(BASE_DIR / "alembic_tenant.ini")

def get_sync_session():
    engine = create_engine(settings.SYNC_DATABASE_URL, echo=False)
    return Session(engine)

def get_current_revision(alembic_cfg, schema_name=None):
    """Obtiene la revisión actual instalada en la BD."""
    try:
        script = ScriptDirectory.from_config(alembic_cfg)
        # Necesitamos un contexto temporal para leer la BD
        # Esto es un hack ligero para leer la versión sin correr migraciones
        from alembic.runtime.migration import MigrationContext
        from sqlalchemy import create_engine
        
        engine = create_engine(settings.SYNC_DATABASE_URL)
        with engine.connect() as conn:
            if schema_name:
                conn.execute(text(f'SET search_path TO "{schema_name}", public'))
            
            context = MigrationContext.configure(conn)
            return context.get_current_revision()
    except Exception:
        return None

def run_public_migrations():
    print("🌍 Aplicando migraciones GLOBALES (schema public)...")
    alembic_cfg = Config(ALEMBIC_GLOBAL_INI)
    alembic_cfg.set_main_option("script_location", "alembic")
    
    # Verificar si ya está al día
    script = ScriptDirectory.from_config(alembic_cfg)
    current = get_current_revision(alembic_cfg)
    head = script.get_current_head()
    
    if current == head:
        print(f"ℹ️  El esquema público ya está actualizado ({current}).")
        return

    try:
        command.upgrade(alembic_cfg, "head")
        print("✅ Migraciones globales aplicadas correctamente.")
    except Exception as e:
        print(f"❌ Error crítico en migraciones públicas: {e}")
        sys.exit(1)

def run_tenant_migrations():
    print("🏢 Iniciando migraciones para TENANTS activos...")
    session = get_sync_session()
    
    try:
        # Asumiendo que tienes una columna is_active, si no, ajusta el filtro
        tenants = session.execute(select(Tenant).where(Tenant.is_active == True)).scalars().all()
        
        if not tenants:
            print("⚠️ No se encontraron tenants activos. Abortando.")
            return

        alembic_cfg = Config(ALEMBIC_TENANT_INI)
        alembic_cfg.set_main_option("script_location", "alembic_tenant")
        
        script = ScriptDirectory.from_config(alembic_cfg)
        head_rev = script.get_current_head()

        for tenant in tenants:
            schema_name = tenant.schema_name
            print(f"\n🔹 Procesando tenant: {schema_name}...")
            
            # Check previo
            current_rev = get_current_revision(alembic_cfg, schema_name)
            if current_rev == head_rev:
                print(f"   ℹ️  {schema_name} ya está al día ({current_rev}). Saltando.")
                continue

            os.environ["TENANT_SCHEMA"] = schema_name
            
            try:
                # Alembic leerá la variable de entorno en env.py
                command.upgrade(alembic_cfg, "head")
                print(f"   ✅ {schema_name} actualizado a {head_rev}.")
            except Exception as e:
                print(f"   ❌ Error en {schema_name}: {e}")
                # Decisión: ¿Continuar con los demás o abortar todo? 
                # Aquí elegimos continuar para no bloquear otros tenants sanos.
            finally:
                # Limpieza estricta
                if "TENANT_SCHEMA" in os.environ:
                    del os.environ["TENANT_SCHEMA"]
            
    except Exception as e:
        print(f"❌ Error general obteniendo tenants: {e}")
    finally:
        session.close()
        
    print("\n🎉 Proceso de migración de tenants finalizado.")

def run_tenant_migrations_stamp(target_revision: str = "head"):
    print(f"🏷️ Sincronizando estado (stamp) para TENANTS a {target_revision}...")
    session = get_sync_session()
    try:
        tenants = session.execute(select(Tenant).where(Tenant.is_active == True)).scalars().all()
        for tenant in tenants:
            schema_name = tenant.schema_name
            print(f" Marcando {schema_name}...")
            
            alembic_cfg = Config(ALEMBIC_TENANT_INI)
            alembic_cfg.set_main_option("script_location", "alembic_tenant")
            os.environ["TENANT_SCHEMA"] = schema_name
            
            try:
                command.stamp(alembic_cfg, target_revision)
                print(f"   ✅ {schema_name} sincronizado a {target_revision}.")
            except Exception as e:
                print(f"   ❌ Error al marcar {schema_name}: {e}")
            finally:
                if "TENANT_SCHEMA" in os.environ:
                    del os.environ["TENANT_SCHEMA"]
    finally:
        session.close()
        if "TENANT_SCHEMA" in os.environ:
            del os.environ["TENANT_SCHEMA"]
        
    print("✅ Sincronización de stamps finalizada.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Gestor de migraciones FastConta")
    parser.add_argument("command", choices=["public", "tenants", "stamp-tenants", "all"], help="Comando a ejecutar")
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