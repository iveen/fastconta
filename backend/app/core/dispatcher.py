"""
Dispatcher de jobs: capa de abstracción para publicación de tareas Celery.

ADR 001 (completado): Todos los jobs pesados se procesan vía Celery.
Este módulo centraliza la lógica de publicación para:
- Facilitar testing (mock del dispatcher)
- Centralizar logging
- Aislar los endpoints del mecanismo de transporte (si cambia el broker, solo se toca aquí)
"""
import logging

logger = logging.getLogger(__name__)


def dispatch_fel_job(
    *,
    job_id: int,
    tenant_id: int,
    empresa_id: int,
    empresa_nit: str,
    schema_name: str,
    user_email: str,
    user_full_name: str,
    xml_files: list[dict],
) -> None:
    """Publica un job FEL a la cola de Celery."""
    from app.tasks.fel_tasks import procesar_fel_zip

    procesar_fel_zip.delay(
        job_id=job_id,
        tenant_id=tenant_id,
        empresa_id=empresa_id,
        empresa_nit=empresa_nit,
        schema_name=schema_name,
        user_email=user_email,
        user_full_name=user_full_name,
        xml_files=xml_files,
    )
    logger.info(
        "📤 Job FEL %d publicado a Celery (tenant=%s, xmls=%d)",
        job_id,
        schema_name,
        len(xml_files),
    )


def dispatch_inventario_job(
    *,
    job_id: int,
    tenant_schema: str,
) -> None:
    """Publica un job de inventario a la cola de Celery."""
    from app.tasks.inventario_tasks import procesar_inventario

    procesar_inventario.delay(
        job_id=job_id,
        tenant_schema=tenant_schema,
    )
    logger.info(
        "📤 Job inventario %d publicado a Celery (tenant=%s)",
        job_id,
        tenant_schema,
    )
def dispatch_tenant_job(
    *,
    tenant_id: int,
    user_id: int,
    schema_name: str,
    admin_email: str,
    admin_password: str,
    company_name: str,
    contact_name: str,
) -> None:
    """Publica un job de provisionamiento de tenant a la cola de Celery."""
    from app.tasks.tenant_tasks import provision_tenant

    provision_tenant.delay(
        tenant_id=tenant_id,
        user_id=user_id,
        schema_name=schema_name,
        admin_email=admin_email,
        admin_password=admin_password,
        company_name=company_name,
        contact_name=contact_name,
    )
    logger.info(
        "📤 Job provisionamiento tenant %d publicado a Celery (schema=%s)",
        tenant_id,
        schema_name,
    )
# ============================================================
# Email dispatchers
# ============================================================

def dispatch_email_fel_completada(
    *,
    to: str,
    full_name: str,
    archivo_nombre: str,
    total_archivos: int,
    facturas_creadas: int,
    facturas_duplicadas: int,
    facturas_con_error: int,
) -> None:
    """Publica email de FEL completada a la cola de Celery."""
    from app.tasks.email_tasks import send_fel_import_completada

    send_fel_import_completada.delay(
        to=to,
        full_name=full_name,
        archivo_nombre=archivo_nombre,
        total_archivos=total_archivos,
        facturas_creadas=facturas_creadas,
        facturas_duplicadas=facturas_duplicadas,
        facturas_con_error=facturas_con_error,
    )
    logger.info("📧 Email FEL completada publicado a Celery (to=%s)", to)


def dispatch_email_fel_fallida(
    *,
    to: str,
    full_name: str,
    archivo_nombre: str,
    error_mensaje: str,
) -> None:
    """Publica email de FEL fallida a la cola de Celery."""
    from app.tasks.email_tasks import send_fel_import_fallida

    send_fel_import_fallida.delay(
        to=to,
        full_name=full_name,
        archivo_nombre=archivo_nombre,
        error_mensaje=error_mensaje,
    )
    logger.info("📧 Email FEL fallida publicado a Celery (to=%s)", to)


def dispatch_email_fel_cancelada(
    *,
    to: str,
    full_name: str,
    archivo_nombre: str,
    archivos_procesados: int,
    archivos_totales: int,
) -> None:
    """Publica email de FEL cancelada a la cola de Celery."""
    from app.tasks.email_tasks import send_fel_import_cancelada

    send_fel_import_cancelada.delay(
        to=to,
        full_name=full_name,
        archivo_nombre=archivo_nombre,
        archivos_procesados=archivos_procesados,
        archivos_totales=archivos_totales,
    )
    logger.info("📧 Email FEL cancelada publicado a Celery (to=%s)", to)


def dispatch_email_importacion_completada(
    *,
    to: str,
    full_name: str,
    archivo_nombre: str,
    periodo: str,
    modo: str,
    filas_procesadas: int,
    filas_validas: int,
    filas_con_error: int,
) -> None:
    """Publica email de importación completada a la cola de Celery."""
    from app.tasks.email_tasks import send_importacion_completada

    send_importacion_completada.delay(
        to=to,
        full_name=full_name,
        archivo_nombre=archivo_nombre,
        periodo=periodo,
        modo=modo,
        filas_procesadas=filas_procesadas,
        filas_validas=filas_validas,
        filas_con_error=filas_con_error,
    )
    logger.info("📧 Email importación completada publicado a Celery (to=%s)", to)


def dispatch_email_importacion_fallida(
    *,
    to: str,
    full_name: str,
    archivo_nombre: str,
    error_mensaje: str,
) -> None:
    """Publica email de importación fallida a la cola de Celery."""
    from app.tasks.email_tasks import send_importacion_fallida

    send_importacion_fallida.delay(
        to=to,
        full_name=full_name,
        archivo_nombre=archivo_nombre,
        error_mensaje=error_mensaje,
    )
    logger.info("📧 Email importación fallida publicado a Celery (to=%s)", to)


def dispatch_email_tenant_aprobado(
    *,
    to: str,
    company_name: str,
    admin_email: str,
    admin_password: str,
    contact_name: str,
) -> None:
    """Publica email de tenant aprobado a la cola de Celery."""
    from app.tasks.email_tasks import send_tenant_aprobado

    send_tenant_aprobado.delay(
        to=to,
        company_name=company_name,
        admin_email=admin_email,
        admin_password=admin_password,
        contact_name=contact_name,
    )
    logger.info("📧 Email tenant aprobado publicado a Celery (to=%s)", to)


def dispatch_email_tenant_rechazado(
    *,
    to: str,
    company_name: str,
    reason: str,
    contact_name: str,
) -> None:
    """Publica email de tenant rechazado a la cola de Celery."""
    from app.tasks.email_tasks import send_tenant_rechazado

    send_tenant_rechazado.delay(
        to=to,
        company_name=company_name,
        reason=reason,
        contact_name=contact_name,
    )
    logger.info("📧 Email tenant rechazado publicado a Celery (to=%s)", to)


def dispatch_email_solicitud_recibida(
    *,
    to: str,
    company_name: str,
    contact_name: str,
) -> None:
    """Publica email de solicitud recibida a la cola de Celery."""
    from app.tasks.email_tasks import send_solicitud_recibida

    send_solicitud_recibida.delay(
        to=to,
        company_name=company_name,
        contact_name=contact_name,
    )
    logger.info("📧 Email solicitud recibida publicado a Celery (to=%s)", to)
