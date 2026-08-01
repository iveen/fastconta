"""
Tareas Celery para envío de emails.

ADR 001 (completado): Todos los emails se envían vía Celery.
Cola dedicada 'email' para no bloquear jobs pesados (FEL, inventario).

Beneficios:
- Retry automático si SMTP falla temporalmente
- Rate limiting contra el proveedor SMTP
- Worker dedicado (no compite con jobs pesados)
- Monitoreo vía Flower
- Si falla el email, el job principal NO falla
"""

import asyncio
import logging

from app.core.celery_app import celery_app
from app.core.email.service import email_service

logger = logging.getLogger(__name__)


# Helper para ejecutar coroutines en Celery
def run_async(coro):
    """Ejecuta una coroutine en un nuevo event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
        asyncio.set_event_loop(None)


# ============================================================
# FEL: Emails de importación de facturas
# ============================================================

@celery_app.task(
    bind=True,
    name="app.tasks.email_tasks.send_fel_import_completada",
    queue="email",
    max_retries=5,
    default_retry_delay=60,
    acks_late=True,
    rate_limit="10/m",
)
def send_fel_import_completada(
    self,
    to: str,
    full_name: str,
    archivo_nombre: str,
    total_archivos: int,
    facturas_creadas: int,
    facturas_duplicadas: int,
    facturas_con_error: int,
) -> dict:
    """Email de éxito al completar importación FEL."""
    try:
        
        
        run_async(
            email_service.send_fel_import_completada(
                to=to,
                full_name=full_name,
                archivo_nombre=archivo_nombre,
                total_archivos=total_archivos,
                facturas_creadas=facturas_creadas,
                facturas_duplicadas=facturas_duplicadas,
                facturas_con_error=facturas_con_error,
            )
        )
        logger.info("📧 Email FEL completada enviado a %s", to)
        return {"status": "sent", "to": to}
    except Exception as exc:
        logger.exception("❌ Error enviando email FEL completada a %s: %s", to, exc)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        return {"status": "failed", "error": str(exc)}


@celery_app.task(
    bind=True,
    name="app.tasks.email_tasks.send_fel_import_fallida",
    queue="email",
    max_retries=5,
    default_retry_delay=60,
    acks_late=True,
    rate_limit="10/m",
)
def send_fel_import_fallida(
    self,
    to: str,
    full_name: str,
    archivo_nombre: str,
    error_mensaje: str,
) -> dict:
    """Email de fallo al procesar importación FEL."""
    try:
        
        
        run_async(
            email_service.send_fel_import_fallida(
                to=to,
                full_name=full_name,
                archivo_nombre=archivo_nombre,
                error_mensaje=error_mensaje,
            )
        )
        logger.info("📧 Email FEL fallida enviado a %s", to)
        return {"status": "sent", "to": to}
    except Exception as exc:
        logger.exception(" Error enviando email FEL fallida a %s: %s", to, exc)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        return {"status": "failed", "error": str(exc)}


@celery_app.task(
    bind=True,
    name="app.tasks.email_tasks.send_fel_import_cancelada",
    queue="email",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
    rate_limit="10/m",
)
def send_fel_import_cancelada(
    self,
    to: str,
    full_name: str,
    archivo_nombre: str,
    archivos_procesados: int,
    archivos_totales: int,
) -> dict:
    """Email de cancelación de importación FEL."""
    try:
        
        
        run_async(
            email_service.send_fel_import_cancelada(
                to=to,
                full_name=full_name,
                archivo_nombre=archivo_nombre,
                archivos_procesados=archivos_procesados,
                archivos_totales=archivos_totales,
            )
        )
        logger.info("📧 Email FEL cancelada enviado a %s", to)
        return {"status": "sent", "to": to}
    except Exception as exc:
        logger.exception("❌ Error enviando email FEL cancelada a %s: %s", to, exc)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        return {"status": "failed", "error": str(exc)}


# ============================================================
# Inventario: Emails de importación
# ============================================================

@celery_app.task(
    bind=True,
    name="app.tasks.email_tasks.send_importacion_completada",
    queue="email",
    max_retries=5,
    default_retry_delay=60,
    acks_late=True,
    rate_limit="10/m",
)
def send_importacion_completada(
    self,
    to: str,
    full_name: str,
    archivo_nombre: str,
    periodo: str,
    modo: str,
    filas_procesadas: int,
    filas_validas: int,
    filas_con_error: int,
) -> dict:
    """Email de éxito al completar importación de inventario."""
    try:
        
        
        run_async(
            email_service.send_importacion_completada(
                to=to,
                full_name=full_name,
                archivo_nombre=archivo_nombre,
                periodo=periodo,
                modo=modo,
                filas_procesadas=filas_procesadas,
                filas_validas=filas_validas,
                filas_con_error=filas_con_error,
            )
        )
        logger.info("📧 Email importación completada enviado a %s", to)
        return {"status": "sent", "to": to}
    except Exception as exc:
        logger.exception("❌ Error enviando email importación completada a %s: %s", to, exc)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        return {"status": "failed", "error": str(exc)}


@celery_app.task(
    bind=True,
    name="app.tasks.email_tasks.send_importacion_fallida",
    queue="email",
    max_retries=5,
    default_retry_delay=60,
    acks_late=True,
    rate_limit="10/m",
)
def send_importacion_fallida(
    self,
    to: str,
    full_name: str,
    archivo_nombre: str,
    error_mensaje: str,
) -> dict:
    """Email de fallo al procesar importación de inventario."""
    try:
        
        
        run_async(
            email_service.send_importacion_fallida(
                to=to,
                full_name=full_name,
                archivo_nombre=archivo_nombre,
                error_mensaje=error_mensaje,
            )
        )
        logger.info(" Email importación fallida enviado a %s", to)
        return {"status": "sent", "to": to}
    except Exception as exc:
        logger.exception("❌ Error enviando email importación fallida a %s: %s", to, exc)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        return {"status": "failed", "error": str(exc)}


# ============================================================
# Tenant: Emails de aprobación, rechazo y solicitudes
# ============================================================

@celery_app.task(
    bind=True,
    name="app.tasks.email_tasks.send_tenant_aprobado",
    queue="email",
    max_retries=5,
    default_retry_delay=120,
    acks_late=True,
    rate_limit="5/m",
)
def send_tenant_aprobado(
    self,
    to: str,
    company_name: str,
    admin_email: str,
    admin_password: str,
    contact_name: str,
) -> dict:
    """Email de aprobación de tenant con credenciales."""
    try:
        
        
        run_async(
            email_service.send_tenant_aprobado(
                to=to,
                company_name=company_name,
                admin_email=admin_email,
                admin_password=admin_password,
                contact_name=contact_name,
            )
        )
        logger.info("📧 Email tenant aprobado enviado a %s", to)
        return {"status": "sent", "to": to}
    except Exception as exc:
        logger.exception("❌ Error enviando email tenant aprobado a %s: %s", to, exc)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        return {"status": "failed", "error": str(exc)}


@celery_app.task(
    bind=True,
    name="app.tasks.email_tasks.send_tenant_rechazado",
    queue="email",
    max_retries=3,
    default_retry_delay=120,
    acks_late=True,
    rate_limit="5/m",
)
def send_tenant_rechazado(
    self,
    to: str,
    company_name: str,
    reason: str,
    contact_name: str,
) -> dict:
    """Email de rechazo de solicitud de tenant."""
    try:
        
        
        run_async(
            email_service.send_tenant_rechazado(
                to=to,
                company_name=company_name,
                reason=reason,
                contact_name=contact_name,
            )
        )
        logger.info("📧 Email tenant rechazado enviado a %s", to)
        return {"status": "sent", "to": to}
    except Exception as exc:
        logger.exception(" Error enviando email tenant rechazado a %s: %s", to, exc)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        return {"status": "failed", "error": str(exc)}


@celery_app.task(
    bind=True,
    name="app.tasks.email_tasks.send_solicitud_recibida",
    queue="email",
    max_retries=3,
    default_retry_delay=120,
    acks_late=True,
    rate_limit="5/m",
)
def send_solicitud_recibida(
    self,
    to: str,
    company_name: str,
    contact_name: str,
) -> dict:
    """Email de confirmación de solicitud recibida."""
    try:
        
        
        run_async(
            email_service.send_solicitud_recibida(
                to=to,
                company_name=company_name,
                contact_name=contact_name,
            )
        )
        logger.info("📧 Email solicitud recibida enviado a %s", to)
        return {"status": "sent", "to": to}
    except Exception as exc:
        logger.exception("❌ Error enviando email solicitud recibida a %s: %s", to, exc)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        return {"status": "failed", "error": str(exc)}
