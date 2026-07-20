"""
Endpoints para importación asíncrona de inventarios.

Flujo:
1. POST /importar → crea job y retorna 202 Accepted
2. GET /jobs/{id} → consulta progreso (polling)
3. GET /jobs → lista jobs del usuario
4. POST /jobs/{id}/cancelar → cancela job pendiente
5. GET /tomas/{id}/historial → historial de importaciones completadas
"""
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.dependencies import resolve_public_id
from app.core.security import DataScope, get_data_scope
from app.db.session import get_tenant_db
from app.models.tenant_models import InventarioImportacion, InventarioToma
from app.schemas.inventario.importacion import (
    ImportacionJobResponse,
    ImportacionResponse,
)
from app.services.inventario import ImportService

from .helpers import importacion_a_response

router = APIRouter()

# Tamaño máximo de archivo: 100MB
MAX_FILE_SIZE = 100 * 1024 * 1024


@router.post(
    "/tomas/{toma_public_id}/importar",
    response_model=ImportacionJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Iniciar importación asíncrona de inventario",
    description=(
        "Sube un archivo xlsx/csv para importar items. "
        "El procesamiento se realiza en background. "
        "Retorna un job_id para consultar el progreso vía polling. "
        "Al finalizar, se envía un correo al usuario con los resultados."
    ),
)
async def importar_inventario(
    toma_public_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    modo: str = Query(
        "REEMPLAZAR",
        pattern="^(REEMPLAZAR|AGREGAR)$",
        description="REEMPLAZAR: borra items actuales; AGREGAR: conserva existentes",
    ),
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    """
    Inicia la importación asíncrona de un archivo de inventario.

    El endpoint retorna inmediatamente con un `job_id`.
    Usa `GET /importaciones/jobs/{job_id}` para consultar el progreso.
    Al finalizar, se envía un correo al usuario con los resultados.
    """
    toma = await resolve_public_id(
        db,
        InventarioToma,
        toma_public_id,
        scope.tenant_id,
        "Toma de inventario no encontrada",
    )

    # Validar extensión del archivo
    filename = (file.filename or "").lower()
    if not filename.endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato no soportado. Use .xlsx, .xls o .csv",
        )

    # Leer contenido del archivo
    file_content = await file.read()

    # Validar tamaño
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Archivo {filename} demasiado grande. Máximo 100MB",
        )

    # Validar que no esté vacío
    if len(file_content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo está vacío",
        )

    svc = ImportService(db)
    try:
        job = await svc.guardar_archivo(
            toma=toma,
            file_content=file_content,
            filename=file.filename or "archivo",
            usuario_id=scope.user.id,
            tenant_schema=scope.tenant_schema,
            modo=modo,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # ✅ Disparar procesamiento en background
    background_tasks.add_task(svc.procesar_job, job.id)

    return ImportacionJobResponse(
        public_id=job.public_id,
        estado=job.estado,
        archivo_original=job.archivo_original,
        tamano_bytes=job.tamano_bytes,
        mensaje=(
            "Importación iniciada. Recibirás un correo al finalizar. "
            "Consulta el progreso en /importaciones/jobs/{job_id}"
        ),
    )


@router.get(
    "/tomas/{toma_public_id}/historial",
    response_model=list[ImportacionResponse],
    summary="Historial de importaciones completadas de una toma",
)
async def listar_importaciones(
    toma_public_id: UUID,
    db: AsyncSession = Depends(get_tenant_db),
    scope: DataScope = Depends(get_data_scope),
):
    """Lista las importaciones completadas de una toma (auditoría)."""
    toma = await resolve_public_id(
        db,
        InventarioToma,
        toma_public_id,
        scope.tenant_id,
        "Toma de inventario no encontrada",
    )
    stmt = (
        select(InventarioImportacion)
        .options(joinedload(InventarioImportacion.toma))
        .where(InventarioImportacion.toma_id == toma.id)
        .order_by(InventarioImportacion.created_at.desc())
    )
    result = await db.execute(stmt)
    importaciones = result.unique().scalars().all()
    return [importacion_a_response(i) for i in importaciones]