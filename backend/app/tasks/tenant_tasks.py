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

from app.core.celery_app import celery_app
from app.core.email.service import email_service
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
    # Timeouts más largos: las migraciones pueden tardar
    soft_time_limit=600,  # 10 min
    time_limit=660,       # 11 min
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
    Si falla, realiza rollback del schema y mantiene el tenant inactivo.
    """
    logger.info(
        "🚀 Iniciando provisionamiento tenant=%d schema='%s'",
        tenant_id,
        schema_name,
    )

    try:
        result = asyncio.run(
            _ejecutar_provisionamiento(
                tenant_id=tenant_id,
                user_id=user_id,
                schema_name=schema_name,
                admin_email=admin_email,
                admin_password=admin_password,
                company_name=company_name,
                contact_name=contact_name,
            )
        )

        logger.info("✅ Tenant %d provisionado exitosamente", tenant_id)
        return result

    except Exception as exc:
        logger.exception(
            "❌ Provisionamiento tenant %d falló: %s",
            tenant_id,
            str(exc),
        )

        # Retry automático para errores transitorios
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
) -> dict:
    """
    Wrapper async que ejecuta el provisionamiento completo.
    """
    from app.db.session import get_public_db_session

    async with get_public_db_session() as db:
        try:
            # 1. Ejecutar migraciones (síncrono, usar to_thread)
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
            logger.info(
                f"✅ Tenant {tenant_id} y User {user_id} activados en BD"
            )

            # 4. Enviar email con credenciales
            try:
                await email_service.send_tenant_aprobado(
                    to=admin_email,
                    company_name=company_name,
                    admin_email=admin_email,
                    admin_password=admin_password,
                    contact_name=contact_name,
                )
                logger.info(f"📧 Email de aprobación enviado a {admin_email}")
            except Exception as e:
                logger.error(f"⚠️ No se pudo enviar email de aprobación: {e}")
                # No fallamos el job por un error de email

            return {"status": "completed", "tenant_id": tenant_id}

        except Exception as e:
            logger.error(
                f"❌ Error en provisionamiento para {schema_name}: {e}"
            )
            # Hacer rollback
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
    from app.db.session import get_public_db_session

    try:
        async with get_public_db_session() as db:
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

    except Exception as cleanup_err:
        logger.error(f"❌ Error crítico en rollback: {cleanup_err}")
