#!/usr/bin/env python3
"""
Script de bootstrap para crear el superadmin inicial de FastConta.

Uso:
    cd backend
    python -m app.scripts.create_superadmin \
        --email admin@fastconta.com \
        --password "PasswordSeguro123!" \
        --full-name "Super Administrador"
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

# ============================================================
# 🔑 CARGAR .env ANTES DE CUALQUIER OTRA IMPORTACIÓN
# ============================================================
from dotenv import load_dotenv
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

SCRIPT_DIR = Path(__file__).resolve().parent
APP_DIR = SCRIPT_DIR.parent
BACKEND_DIR = APP_DIR.parent
ENV_FILE = BACKEND_DIR / ".env"

if not ENV_FILE.exists():
    print(f"❌ Error: No se encontró .env en {ENV_FILE}")
    print(f"   Asegúrate de ejecutar el script desde: {BACKEND_DIR}")
    sys.exit(1)

load_dotenv(ENV_FILE)
print(f"✅ .env cargado desde: {ENV_FILE}")

# Agregar backend/ al path
sys.path.insert(0, str(BACKEND_DIR))

# ============================================================
# IMPORTS (después de cargar .env)
# ============================================================
from app.core.security import get_password_hash  # noqa: E402

# ✅ CORREGIDO: Usar AsyncSessionLocal (como en seed_categorias_activos.py)
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.models.global_models import Role, Tenant, User  # noqa: E402

# ============================================================
# CONFIGURACIÓN
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SYSTEM_TENANT_NAME = "Sistema"
SYSTEM_TENANT_NIT = "0000000-0"
SYSTEM_TENANT_SCHEMA = "system"
SYSTEM_TENANT_PLAN = "enterprise"


# ============================================================
# FUNCIONES
# ============================================================
async def ensure_system_tenant(db: AsyncSession) -> Tenant:
    """Crea el tenant 'system' si no existe."""
    result = await db.execute(
        select(Tenant).where(Tenant.schema_name == SYSTEM_TENANT_SCHEMA)
    )
    tenant = result.scalar_one_or_none()
    
    if tenant:
        logger.info(f"✅ Tenant 'system' ya existe (id={tenant.id})")
        return tenant
    
    # Crear schema del tenant system
    await db.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{SYSTEM_TENANT_SCHEMA}"'))
    logger.info(f"📁 Schema '{SYSTEM_TENANT_SCHEMA}' creado")
    
    # Crear el tenant en la tabla public.tenants
    tenant = Tenant(
        name=SYSTEM_TENANT_NAME,
        nit=SYSTEM_TENANT_NIT,
        schema_name=SYSTEM_TENANT_SCHEMA,
        admin_email="system@fastconta.internal",
        plan=SYSTEM_TENANT_PLAN,
        max_usuarios=999999,
        is_active=True
    )
    db.add(tenant)
    await db.flush()
    logger.info(f"✅ Tenant 'system' creado (id={tenant.id}, public_id={tenant.public_id})")
    return tenant


async def ensure_superadmin_role(db: AsyncSession) -> Role:
    """Verifica que el rol superadmin existe."""
    result = await db.execute(
        select(Role).where(Role.codigo == "superadmin")
    )
    role = result.scalar_one_or_none()
    
    if not role:
        raise RuntimeError(
            "❌ El rol 'superadmin' no existe. "
            "Ejecuta primero: alembic -c alembic.ini upgrade head"
        )
    
    logger.info(f"✅ Rol 'superadmin' encontrado (id={role.id})")
    return role


async def create_superadmin(
    db: AsyncSession,
    email: str,
    password: str,
    full_name: str,
    tenant: Tenant,
    role: Role
) -> User:
    """Crea el usuario superadmin."""
    result = await db.execute(
        select(User).where(User.email == email)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        logger.warning(f"⚠️  Ya existe un usuario con email {email}")
        return existing
    
    user = User(
        tenant_id=tenant.id,
        email=email,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        role_id=role.id,
        is_active=True
    )
    db.add(user)
    await db.flush()
    logger.info(f"✅ Superadmin creado: {email} (id={user.id}, public_id={user.public_id})")
    return user


async def main(email: str, password: str, full_name: str):
    """Flujo principal de bootstrap."""
    logger.info("=" * 60)
    logger.info("🚀 Iniciando bootstrap de superadmin...")
    logger.info("=" * 60)
    
    # ✅ CORREGIDO: Usar AsyncSessionLocal() como contexto
    async with AsyncSessionLocal() as db:
        try:
            tenant = await ensure_system_tenant(db)
            role = await ensure_superadmin_role(db)
            user = await create_superadmin(db, email, password, full_name, tenant, role)
            
            await db.commit()
            
            logger.info("=" * 60)
            logger.info("🎉 Bootstrap completado exitosamente!")
            logger.info("=" * 60)
            logger.info(f"📧 Email: {user.email}")
            logger.info(f"🆔 User ID (interno): {user.id}")
            logger.info(f"🆔 User Public ID: {user.public_id}")
            logger.info(f"🏢 Tenant: {tenant.name}")
            logger.info(f"🏢 Schema: {tenant.schema_name}")
            logger.info(f"🔑 Rol: {role.codigo}")
            logger.info("=" * 60)
            logger.info("⚠️  Guarda estas credenciales en un lugar seguro.")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Error durante el bootstrap: {e}")
            raise


# ============================================================
# CLI
# ============================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Crear el superadmin inicial de FastConta"
    )
    parser.add_argument("--email", required=True, help="Email del superadmin")
    parser.add_argument("--password", required=True, help="Password (mínimo 8 caracteres)")
    parser.add_argument("--full-name", required=True, help="Nombre completo")
    
    args = parser.parse_args()
    
    if len(args.password) < 8:
        logger.error("❌ El password debe tener al menos 8 caracteres")
        sys.exit(1)
    
    try:
        asyncio.run(main(args.email, args.password, args.full_name))
    except KeyboardInterrupt:
        logger.info("\n⚠️  Bootstrap cancelado")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        sys.exit(1)