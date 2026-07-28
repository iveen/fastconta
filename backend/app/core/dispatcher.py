"""
Dispatcher de jobs: abstrae la decisión entre Celery y BackgroundTasks.
"""
import logging

from fastapi import BackgroundTasks
from sqlalchemy import text

from app.config import settings
from app.db.base import AsyncSessionLocal
from app.services.fel.zip_processor import FELZipProcessor
from app.services.inventario import ImportService

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
    if settings.USE_CELERY:
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
        logger.info("📤 Job FEL %d publicado a Celery (tenant=%s, xmls=%d)", job_id, schema_name, len(xml_files))
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
        logger.info("📤 Job FEL %d programado en BackgroundTasks (tenant=%s, xmls=%d)", job_id, schema_name, len(xml_files))
        return "background"


def dispatch_inventario_job(
    background_tasks: BackgroundTasks,
    *,
    job_id: int,
    tenant_schema: str,
) -> str:
    if settings.USE_CELERY:
        from app.tasks.inventario_tasks import procesar_inventario

        procesar_inventario.delay(
            job_id=job_id,
            tenant_schema=tenant_schema,
        )
        logger.info("📤 Job inventario %d publicado a Celery (tenant=%s)", job_id, tenant_schema)
        return "celery"
    else:
        async def _procesar_background():
            async with AsyncSessionLocal() as bg_db:
                await bg_db.execute(text(f"SET LOCAL search_path TO {tenant_schema}, public"))
                svc = ImportService(bg_db)
                await svc.procesar_job(job_id)

        background_tasks.add_task(_procesar_background)
        logger.info("📤 Job inventario %d programado en BackgroundTasks (tenant=%s)", job_id, tenant_schema)
        return "background"
