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

from app.core.celery_app import celery_app

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
        result = asyncio.run(_ejecutar_import_service(job_id, tenant_schema))

        logger.info("✅ Job inventario %d completado: %s", job_id, result)
        return result

    except Exception as exc:
        logger.exception("❌ Job inventario %d falló con error: %s", job_id, str(exc))

        # Retry automático para errores transitorios
        if self.request.retries < self.max_retries:
            logger.warning(
                "🔄 Reintentando job inventario %d (intento %d/%d)...",
                job_id,
                self.request.retries + 1,
                self.max_retries,
            )
            raise self.retry(exc=exc)

        # Nota: NO necesitamos marcar el job como FALLIDO aquí.
        # ImportService._marcar_fallido() ya lo hace internamente cuando hay excepción.
        return {"status": "failed", "error": str(exc)}


async def _ejecutar_import_service(job_id: int, tenant_schema: str) -> dict:
    """
    Wrapper async que ejecuta ImportService.procesar_job.
    """
    # Imports diferidos para evitar carga circular o overhead innecesario
    from app.db.base import AsyncSessionLocal
    from app.services.inventario import ImportService

    # Creamos una sesión "dummy" porque el constructor de ImportService la exige.
    # procesar_job() la ignorará y creará la suya propia con el search_path correcto.
    async with AsyncSessionLocal() as db:
        svc = ImportService(db)
        await svc.procesar_job(job_id)

    return {"status": "completed", "job_id": job_id}
