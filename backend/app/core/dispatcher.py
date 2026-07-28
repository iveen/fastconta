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
