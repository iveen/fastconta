"""
Tareas Celery para procesamiento de facturas FEL.

ADR 001: Reemplazo de BackgroundTasks con Redis + Celery.

Consideraciones:
- Celery workers son síncronos, pero FELZipProcessor es async.
  Usamos asyncio.run() como bridge.
- Cada tarea configura su propio search_path para aislamiento multi-tenant.
- Los workers comparten el volumen de uploads con el backend (temp files).
"""

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.celery_app import celery_app
from app.db.base import create_celery_engine
from app.services.fel.zip_processor import FELZipProcessor

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.fel_tasks.procesar_fel_zip",
    queue="fel",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
    rate_limit="30/m",
)
def procesar_fel_zip(
    self,
    job_id: int,
    tenant_id: int,
    empresa_id: int,
    empresa_nit: str,
    schema_name: str,
    user_email: str,
    user_full_name: str,
    xml_files: list[dict],
):
    """
    Procesa un ZIP de facturas FEL en background.
    Crea su propio engine de BD para no compartir el pool con FastAPI.
    """
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
                _ejecutar_processor(
                    job_id=job_id,
                    tenant_id=tenant_id,
                    empresa_id=empresa_id,
                    empresa_nit=empresa_nit,
                    schema_name=schema_name,
                    user_email=user_email,
                    user_full_name=user_full_name,
                    xml_files=xml_files,
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
        logger.error(f"❌ Job FEL {job_id} falló con error: {exc}", exc_info=True)
        if self.request.retries < self.max_retries:
            logger.info(f"🔄 Reintentando job {job_id} (intento {self.request.retries + 1}/{self.max_retries})...")
            raise self.retry(exc=exc)
        return {"status": "failed", "error": str(exc)}


async def _ejecutar_processor(
    job_id: int,
    tenant_id: int,
    empresa_id: int,
    empresa_nit: str,
    schema_name: str,
    user_email: str,
    user_full_name: str,
    xml_files: list[dict],
    session_factory,
):
    """Wrapper async para el procesador de ZIPs."""
    await FELZipProcessor.process_job(
        job_id=job_id,
        tenant_id=tenant_id,
        empresa_id=empresa_id,
        empresa_nit=empresa_nit,
        schema_name=schema_name,
        user_email=user_email,
        user_full_name=user_full_name,
        xml_files=xml_files,
        session_factory=session_factory,
    )
    return {"status": "completed", "job_id": job_id}
