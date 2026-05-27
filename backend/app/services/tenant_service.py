# app/services/tenant_service.py
import uuid
import os
from sqlalchemy.orm import Session
from sqlalchemy import text
from alembic.config import Config
from alembic import command
from app.models.global_models import Tenant

# Apunta correctamente a la raíz de tus archivos .ini
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ALEMBIC_TENANT_INI = os.path.join(BASE_DIR, "alembic_tenant.ini")

def crear_nuevo_tenant_sistema(db: Session, nombre_comercial: str, nit: str) -> Tenant:
    """
    Orquesta la creación completa de un tenant: registro en public, 
    creación física del esquema y ejecución de migraciones base.
    """
    nuevo_id = uuid.uuid4()
    schema_seguro = f"t_{nuevo_id.hex}"  # Genera t_550e8400e29b41d4a716446655440000
    
    # 1. Crear el objeto en el esquema public
    nuevo_tenant = Tenant(
        id=nuevo_id,
        name=nombre_comercial,
        schema_name=schema_seguro,
        nit=nit,
        plan="freemium"
    )
    db.add(nuevo_tenant)
    db.flush()  # Pre-salva en la transacción sin confirmar (commit) todavía
    
    try:
        # 2. Crear el esquema físico en PostgreSQL de forma segura
        # Al usar variables internas controladas (t_hex), evitamos inyección SQL
        db.execute(text(f'CREATE SCHEMA "{schema_seguro}";'))
        
        # 3. Confirmamos la creación del registro y del esquema
        db.commit()
        db.refresh(nuevo_tenant)
        
        # 4. Correr las migraciones de Alembic para el nuevo esquema
        # Nota: En producción, es ideal delegar esto a un worker (Celery/Arq) 
        # para no bloquear el request de FastAPI, pero para desarrollo/MVP funciona directo:
        ejecutar_migraciones_nuevo_tenant(schema_seguro)
        
        return nuevo_tenant

    except Exception as e:
        db.rollback()
        # Si falló la creación del esquema o migraciones, eliminamos el esquema por seguridad si se llegó a crear
        with db.get_bind().connect() as conn:
            conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_seguro}" CASCADE;'))
        raise e

def ejecutar_migraciones_nuevo_tenant(schema_name: str):
    """
    Función síncrona que configura dinámicamente el entorno de Alembic
    y ejecuta 'upgrade head' para poblar el esquema del nuevo tenant.
    """
    alembic_cfg = Config(ALEMBIC_TENANT_INI)
    alembic_cfg.set_main_option("script_location", "alembic_tenant")
    
    # Inyectamos de forma segura el scope del nuevo esquema para que env.py lo lea
    os.environ["TENANT_SCHEMA"] = schema_name
    try:
        command.upgrade(alembic_cfg, "head")
    finally:
        # Limpieza estricta de variables de entorno para evitar colisiones
        if "TENANT_SCHEMA" in os.environ:
            del os.environ["TENANT_SCHEMA"]