"""
Tareas Celery para procesamiento de importaciones de inventario.
ADR 001: Reemplazo de BackgroundTasks con Redis + Celery.

Nota de diseño:
ImportService.procesar_job() crea su propia sesión de BD internamente 
(lee tenant_schema del job en BD y configura search_path). 
La sesión que pasamos al constructor es solo para satisfacer la firma, 
pero procesar_job() la ignora y usa la suya propia.
"""

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.celery_app import celery_app
from app.db.base import create_celery_engine

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.inventario_tasks.procesar_inventario",
    queue="inventario",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def procesar_inventario(
    self,
    job_id: int,
    tenant_schema: str,
) -> dict:
    """
    Tarea Celery que procesa una importación de inventario.
    """
    logger.info(
        "🚀 Iniciando procesamiento inventario job=%d tenant=%s",
        job_id,
        tenant_schema,
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
                _ejecutar_import_service(job_id, tenant_schema, CelerySessionLocal)
            )
            return result
        finally:
            # ✅ Cerrar el engine y el loop
            loop.run_until_complete(celery_engine.dispose())
            loop.close()
            asyncio.set_event_loop(None)
            
    except Exception as exc:
        logger.exception("❌ Job inventario %d falló con error: %s", job_id, str(exc))
        if self.request.retries < self.max_retries:
            logger.warning(
                "🔄 Reintentando job inventario %d (intento %d/%d)...",
                job_id,
                self.request.retries + 1,
                self.max_retries,
            )
            raise self.retry(exc=exc)
        return {"status": "failed", "error": str(exc)}


async def _ejecutar_import_service(
    job_id: int, 
    tenant_schema: str,
    session_factory,
) -> dict:
    """
    Wrapper async que ejecuta ImportService.procesar_job.
    """
    from app.services.inventario import ImportService
    
    # Crear sesión con el factory proporcionado
    async with session_factory() as db:
        svc = ImportService(db, tenant_schema=tenant_schema)
        await svc.procesar_job(job_id)
    
    return {"status": "completed", "job_id": job_id}
