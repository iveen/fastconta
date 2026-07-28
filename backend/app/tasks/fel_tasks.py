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
from datetime import UTC, datetime

from sqlalchemy import text

from app.core.celery_app import celery_app
from app.db.session import get_public_db_session
from app.services.fel.zip_processor import FELZipProcessor

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.fel_tasks.procesar_fel_zip",
    queue="fel",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
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
) -> dict:
    """
    Tarea Celery que procesa un ZIP de facturas FEL.

    Esta es la versión Celery de FELZipProcessor.process_job.
    Se ejecuta en un worker separado del servidor web.

    Args:
        job_id: ID del FELImportJob en la BD.
        tenant_id: ID del tenant (firma contable).
        empresa_id: ID de la empresa dentro del tenant.
        empresa_nit: NIT de la empresa (sin guiones).
        schema_name: Nombre del schema PostgreSQL del tenant.
        user_email: Email del usuario que subió el ZIP.
        user_full_name: Nombre completo del usuario.
        xml_files: Lista de dicts con {filename, xml_text, raw_bytes}.

    Returns:
        dict con resumen del procesamiento.
    """
    logger.info(
        "🚀 Iniciando procesamiento FEL job=%d tenant=%s xmls=%d",
        job_id,
        schema_name,
        len(xml_files),
    )

    try:
        # Bridge async → sync: Celery es síncrono, nuestro processor es async
        result = asyncio.run(
            _ejecutar_processor(
                job_id=job_id,
                tenant_id=tenant_id,
                empresa_id=empresa_id,
                empresa_nit=empresa_nit,
                schema_name=schema_name,
                user_email=user_email,
                user_full_name=user_full_name,
                xml_files=xml_files,
            )
        )

        logger.info(
            "✅ Job FEL %d completado: %s",
            job_id,
            result,
        )
        return result

    except Exception as exc:
        logger.exception(
            "❌ Job FEL %d falló con error: %s",
            job_id,
            str(exc),
        )

        # Retry automático para errores transitorios
        if self.request.retries < self.max_retries:
            logger.warning(
                "🔄 Reintentando job %d (intento %d/%d)...",
                job_id,
                self.request.retries + 1,
                self.max_retries,
            )
            raise self.retry(exc=exc)

        # Si agotamos los retries, marcamos el job como fallido
        asyncio.run(_marcar_job_fallido(job_id, schema_name, str(exc)))
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
) -> dict:
    """
    Wrapper async que ejecuta FELZipProcessor.process_job.

    Crea su propia sesión de BD porque el worker Celery es un proceso
    separado del servidor web.
    """
    await FELZipProcessor.process_job(
        job_id=job_id,
        tenant_id=tenant_id,
        empresa_id=empresa_id,
        empresa_nit=empresa_nit,
        schema_name=schema_name,
        user_email=user_email,
        user_full_name=user_full_name,
        xml_files=xml_files,
    )
    return {"status": "completed", "job_id": job_id}


async def _marcar_job_fallido(
    job_id: int,
    schema_name: str,
    error_message: str,
) -> None:
    """
    Marca un job como FALLIDO en la BD cuando se agotan los retries.
    """


    try:
        async with get_public_db_session() as db:
            await db.execute(
                text(
                    "UPDATE fel_import_jobs "
                    "SET estado = 'FALLIDO', "
                    "    mensaje_error = :msg, "
                    "    finalizado_en = :now "
                    "WHERE id = :jid"
                ),
                {
                    "msg": f"Error tras reintentos: {error_message[:500]}",
                    "now": datetime.now(UTC),
                    "jid": job_id,
                },
            )
            await db.commit()
            logger.info("📝 Job %d marcado como FALLIDO en BD", job_id)
    except Exception as db_exc:
        logger.exception(
            "⚠️ No se pudo marcar job %d como fallido: %s",
            job_id,
            str(db_exc),
        )
