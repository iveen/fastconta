"""
Tareas Celery para provisionamiento de tenants.
ADR 001: Reemplazo de BackgroundTasks con Redis + Celery.

Este job es especial porque:
- Ejecuta migraciones de BD (síncrono, puede tardar 10-30s)
- Requiere rollback manual si falla (limpia schema de Postgres)
- Envía email con credenciales al admin del nuevo tenant
"""

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.celery_app import celery_app
from app.core.dispatcher import dispatch_email_tenant_aprobado
from app.db.base import create_celery_engine
from app.models.global_models import Tenant, User
from app.services.base.tenant_setup import (
    cleanup_tenant_schema,
    initialize_tenant_schema,
)

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.tenant_tasks.provision_tenant",
    queue="tenant",
    max_retries=2,
    default_retry_delay=120,
    acks_late=True,
    soft_time_limit=600,
    time_limit=660,
)
def provision_tenant(
    self,
    tenant_id: int,
    user_id: int,
    schema_name: str,
    admin_email: str,
    admin_password: str,
    company_name: str,
    contact_name: str,
) -> dict:
    """
    Tarea Celery para ejecutar migraciones y notificar al usuario.
    """
    logger.info(
        "🚀 Iniciando provisionamiento tenant=%d schema='%s'",
        tenant_id,
        schema_name,
    )
    try:
        # ✅ Crear un nuevo event loop para esta tarea
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # ✅ Crear engine INDEPENDIENTE dentro del loop
            celery_engine = create_celery_engine()
            CelerySessionLocal = async_sessionmaker(
                bind=celery_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            
            result = loop.run_until_complete(
                _ejecutar_provisionamiento(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    schema_name=schema_name,
                    admin_email=admin_email,
                    admin_password=admin_password,
                    company_name=company_name,
                    contact_name=contact_name,
                    session_factory=CelerySessionLocal,
                )
            )
            return result
        finally:
            # ✅ Cerrar el engine y el loop
            loop.run_until_complete(celery_engine.dispose())
            loop.close()
            asyncio.set_event_loop(None)
            
    except Exception as exc:
        logger.exception(
            "❌ Provisionamiento tenant %d falló: %s",
            tenant_id,
            str(exc),
        )
        if self.request.retries < self.max_retries:
            logger.warning(
                "🔄 Reintentando provisionamiento tenant %d (intento %d/%d)...",
                tenant_id,
                self.request.retries + 1,
                self.max_retries,
            )
            raise self.retry(exc=exc)
        # Si agotamos los retries, hacer rollback completo
        asyncio.run(
            _rollback_provisionamiento(
                tenant_id=tenant_id,
                user_id=user_id,
                schema_name=schema_name,
            )
        )
        return {"status": "failed", "error": str(exc)}


async def _ejecutar_provisionamiento(
    tenant_id: int,
    user_id: int,
    schema_name: str,
    admin_email: str,
    admin_password: str,
    company_name: str,
    contact_name: str,
    session_factory,
) -> dict:
    """
    Wrapper async que ejecuta el provisionamiento completo.
    """
    async with session_factory() as db:
        try:
            # 1. Ejecutar migraciones
            logger.info(f"🔨 Ejecutando migraciones para '{schema_name}'")
            await asyncio.to_thread(initialize_tenant_schema, schema_name)
            logger.info(f"✅ Migraciones completadas para '{schema_name}'")
            
            # 2. Activar tenant
            tenant = (
                await db.execute(select(Tenant).where(Tenant.id == tenant_id))
            ).scalar_one_or_none()
            if tenant:
                tenant.is_active = True
                logger.info(f"✅ Tenant {tenant_id} activado")
            
            # 3. Activar usuario
            user = (
                await db.execute(select(User).where(User.id == user_id))
            ).scalar_one_or_none()
            if user:
                user.is_active = True
                logger.info(f"✅ User {user_id} activado")
            
            await db.commit()
            logger.info(f"✅ Tenant {tenant_id} y User {user_id} activados en BD")
            
            # 4. Enviar email con credenciales
            try:
                dispatch_email_tenant_aprobado(
                    to=admin_email,
                    company_name=company_name,
                    admin_email=admin_email,
                    admin_password=admin_password,
                    contact_name=contact_name,
                )
                logger.info(f"📧 Email de aprobación enviado a {admin_email}")
            except Exception as e:
                logger.error(f"⚠️ No se pudo enviar email de aprobación: {e}")
            
            return {"status": "completed", "tenant_id": tenant_id}
        except Exception as e:
            logger.error(f"❌ Error en provisionamiento para {schema_name}: {e}")
            await _rollback_provisionamiento(
                tenant_id=tenant_id,
                user_id=user_id,
                schema_name=schema_name,
            )
            raise


async def _rollback_provisionamiento(
    tenant_id: int,
    user_id: int,
    schema_name: str,
) -> None:
    """
    Rollback: desactiva registros y limpia schema en Postgres.
    """
    try:
        # ✅ Crear engine independiente para el rollback
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            celery_engine = create_celery_engine()
            CelerySessionLocal = async_sessionmaker(
                bind=celery_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            
            async with CelerySessionLocal() as db:
                tenant = (
                    await db.execute(select(Tenant).where(Tenant.id == tenant_id))
                ).scalar_one_or_none()
                if tenant:
                    tenant.is_active = False
                
                user = (
                    await db.execute(select(User).where(User.id == user_id))
                ).scalar_one_or_none()
                if user:
                    user.is_active = False
                
                await db.commit()
            
            # Limpiar schema fallido
            await asyncio.to_thread(cleanup_tenant_schema, schema_name)
            logger.info(f"🗑️ Rollback de schema '{schema_name}' completado")
        finally:
            loop.run_until_complete(celery_engine.dispose())
            loop.close()
            asyncio.set_event_loop(None)
    except Exception as cleanup_err:
        logger.error(f"❌ Error crítico en rollback: {cleanup_err}")
