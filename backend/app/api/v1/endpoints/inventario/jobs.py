"""
Endpoints para gestión de jobs de importación.

Flujos:
- Usuario normal: consultar sus jobs, cancelar jobs pendientes
- Superadmin: monitoreo global de todos los jobs del sistema
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import resolve_public_id_global
from app.core.security import DataScope, get_data_scope, require_role
from app.db.session import get_public_db, get_tenant_db
from app.models.global_models import InventarioImportacionJob
from app.schemas.inventario.importacion import ImportacionJobResponse
from app.services.inventario import JobService

router = APIRouter()


def _job_a_response(job: InventarioImportacionJob) -> ImportacionJobResponse:
    """Helper para convertir un job ORM a response."""
    return ImportacionJobResponse(
        public_id=job.public_id,
        estado=job.estado,
        archivo_original=job.archivo_original,
        tamano_bytes=job.tamano_bytes,
        filas_totales=job.filas_totales,
        filas_procesadas=job.filas_procesadas,
        filas_validas=job.filas_validas,
        filas_con_error=job.filas_con_error,
        porcentaje=job.porcentaje,
        mensaje_error=job.mensaje_error,
        importacion_public_id=(
            str(job.importacion_id) if job.importacion_id else None
        ),
        iniciado_en=job.iniciado_en,
        finalizado_en=job.finalizado_en,
    )


# ============================================================
# ENDPOINTS PARA USUARIO NORMAL
# ============================================================


@router.get(
    "/jobs",
    response_model=list[ImportacionJobResponse],
    summary="Listar jobs de importación del usuario",
    description="Lista los jobs de importación más recientes del usuario autenticado.",
)
async def listar_jobs_usuario(
    limit: int = Query(20, ge=1, le=100, description="Máximo de resultados"),
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    """
    Lista los jobs de importación recientes del usuario autenticado.

    Útil para mostrar en el frontend una lista de importaciones en progreso
    o completadas recientemente.
    """
    svc = JobService(db)
    jobs = await svc.listar_por_usuario(
        usuario_id=scope.user.id,
        tenant_id=scope.tenant_id,
        limit=limit,
    )
    return [_job_a_response(j) for j in jobs]


@router.get(
    "/jobs/{job_public_id}",
    response_model=ImportacionJobResponse,
    summary="Consultar estado de un job",
    description="Consulta el estado actual de un job de importación (para polling).",
)
async def consultar_estado_job(
    job_public_id: UUID,
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    """
    Consulta el estado actual de un job de importación.

    Estados posibles:
    - PENDIENTE: job creado, esperando ejecución
    - PROCESANDO: archivo siendo procesado
    - COMPLETADO: importación finalizada exitosamente
    - FALLIDO: error durante el procesamiento
    - CANCELADO: cancelado por el usuario antes de procesarse
    - TOMA_ELIMINADA: la toma asociada fue eliminada
    """
    svc = JobService(db)
    job = await svc.obtener_por_public_id(str(job_public_id))

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job no encontrado",
        )

    # Validar que el job pertenezca al tenant del usuario
    # (o que sea superadmin)
    if scope.role_code != "superadmin" and job.tenant_id != scope.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job no encontrado",
        )

    # Validar que el job pertenezca al usuario (excepto superadmin)
    if scope.role_code != "superadmin" and job.usuario_id != scope.user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job no encontrado",
        )

    return _job_a_response(job)


@router.post(
    "/jobs/{job_public_id}/cancelar",
    response_model=ImportacionJobResponse,
    summary="Cancelar un job pendiente",
    description=(
        "Cancela un job que aún no ha empezado a procesarse. "
        "Solo jobs en estado PENDIENTE pueden ser cancelados."
    ),
)
async def cancelar_job(
    job_public_id: UUID,
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    """
    Cancela un job de importación pendiente.

    Solo se pueden cancelar jobs en estado PENDIENTE.
    Si el job ya está PROCESANDO, no se puede cancelar porque
    ya hay datos insertados en la base de datos.
    """
    svc = JobService(db)
    job = await svc.obtener_por_public_id(str(job_public_id))

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job no encontrado",
        )

    # Validar que el job pertenezca al usuario
    if job.usuario_id != scope.user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job no encontrado",
        )

    try:
        job_cancelado = await svc.cancelar(job, scope.user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return _job_a_response(job_cancelado)


# ============================================================
# ENDPOINTS PARA SUPERADMIN (Monitoreo global)
# ============================================================


@router.get(
    "/admin/jobs",
    response_model=list[ImportacionJobResponse],
    summary="Listar todos los jobs (superadmin)",
    description=(
        "Endpoint exclusivo para superadmin. Lista todos los jobs "
        "de importación del sistema, con filtros opcionales."
    ),
    dependencies=[Depends(require_role("superadmin"))],
)
async def listar_jobs_global(
    tenant_id: int | None = Query(None, description="Filtrar por tenant"),
    estado: str | None = Query(
        None,
        description="Filtrar por estado: PENDIENTE, PROCESANDO, COMPLETADO, FALLIDO, CANCELADO, TOMA_ELIMINADA",
    ),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de resultados"),
    db: AsyncSession = Depends(get_public_db),
):
    """
    Lista todos los jobs de importación del sistema.

    Solo accesible para superadmin. Permite filtrar por tenant y estado
    para monitoreo y debugging.
    """
    svc = JobService(db)
    jobs = await svc.listar_global(
        tenant_id=tenant_id,
        estado=estado,
        limit=limit,
    )
    return [_job_a_response(j) for j in jobs]


@router.get(
    "/admin/jobs/estadisticas",
    summary="Estadísticas globales de jobs (superadmin)",
    description="Retorna conteos de jobs por estado para el dashboard de superadmin.",
    dependencies=[Depends(require_role("superadmin"))],
)
async def estadisticas_jobs_global(
    tenant_id: int | None = Query(None, description="Filtrar por tenant"),
    db: AsyncSession = Depends(get_public_db),
):
    """
    Obtiene estadísticas globales de jobs de importación.

    Retorna conteos por estado:
    - pendientes: jobs esperando ejecución
    - procesando: jobs en ejecución
    - completados: jobs finalizados exitosamente
    - fallidos: jobs con errores
    - cancelados: jobs cancelados por usuarios
    - toma_eliminada: jobs cuya toma fue eliminada
    - total: total de jobs en el sistema
    """
    svc = JobService(db)
    return await svc.obtener_estadisticas(tenant_id=tenant_id)


@router.get(
    "/admin/jobs/{job_public_id}",
    response_model=ImportacionJobResponse,
    summary="Consultar cualquier job (superadmin)",
    description="Endpoint exclusivo para superadmin para consultar cualquier job del sistema.",
    dependencies=[Depends(require_role("superadmin"))],
)
async def consultar_job_admin(
    job_public_id: UUID,
    db: AsyncSession = Depends(get_public_db),
):
    """
    Consulta los detalles completos de cualquier job del sistema.

    Solo accesible para superadmin. Útil para debugging y soporte.
    """
    job = await resolve_public_id_global(
        db,
        InventarioImportacionJob,
        job_public_id,
        "Job no encontrado",
    )
    return _job_a_response(job)