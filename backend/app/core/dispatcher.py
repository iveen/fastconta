"""
Dispatcher de jobs: abstrae la decisión entre Celery y BackgroundTasks.

Permite migración gradual mediante el feature flag USE_CELERY.
Cuando USE_CELERY=True → publica a Redis/Celery.
Cuando USE_CELERY=False → usa BackgroundTasks de FastAPI (comportamiento actual).

Esto permite:
- Rollback instantáneo sin redeploy (solo cambiar la variable de entorno)
- Coexistencia de ambos sistemas durante la transición
- Testing A/B en staging
"""
import logging

from fastapi import BackgroundTasks

from app.config import settings
from app.services.fel.zip_processor import FELZipProcessor
from app.tasks.fel_tasks import procesar_fel_zip

logger = logging.getLogger(__name__)


def dispatch_fel_job(
    background_tasks: BackgroundTasks,
    *,
    job_id: int,
    tenant_id: int,
    empresa_id: int,
    empresa_nit: str,
    schema_name: str,
    user_email: str,
    user_full_name: str,
    xml_files: list[dict],
) -> str:
    """
    Despacha un job de procesamiento FEL al backend adecuado.

    Returns:
        str: "celery" o "background" según el backend utilizado.
    """
    if settings.USE_CELERY:
        # Import diferido para evitar cargar Celery cuando no se usa

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
        return "celery"
    else:
        

        background_tasks.add_task(
            FELZipProcessor.process_job,
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
            "📤 Job FEL %d programado en BackgroundTasks (tenant=%s, xmls=%d)",
            job_id,
            schema_name,
            len(xml_files),
        )
        return "background"
