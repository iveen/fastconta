"""
Endpoints para gestión de jobs de importación FEL.
"""
import logging
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import DataScope, get_data_scope
from app.db.session import get_public_db
from app.dependencies.empresa import get_active_empresa
from app.models.global_models import FELImportJob
from app.models.tenant_models import Empresa
from app.schemas.fel.job import FELImportJobResponse, FELJobCreatedResponse
from app.services.fel.zip_processor import FELZipProcessor

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# HELPER: Configurar search_path según rol
# ============================================================
async def _set_schema_for_query(
    db: AsyncSession,
    scope: DataScope,
    tenant_id: int | None = None,
) -> str:
    """Configura el search_path correcto según el rol del usuario."""
    if scope.role_code == "superadmin":
        if not tenant_id:
            raise HTTPException(400, detail="Superadmin debe especificar un tenant_id")
        res = await db.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"),
            {"tid": tenant_id},
        )
    else:
        res = await db.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"),
            {"tid": scope.tenant_id},
        )
    row = res.first()
    if not row:
        raise HTTPException(404, detail="Tenant no encontrado")
    schema_name = row[0]
    if not schema_name.replace("_", "").isalnum():
        raise HTTPException(500, detail="Schema con formato inválido")
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    return schema_name


# ============================================================
# 1. Listar jobs recientes del tenant/empresa
# ============================================================
@router.get("", response_model=List[FELImportJobResponse])
async def list_fel_jobs(
    empresa_id: int | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    estado: str | None = Query(None),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
    empresa_from_header: Empresa | None = Depends(get_active_empresa),
):
    """Lista los jobs de importación FEL recientes."""
    empresa_id_final = empresa_id or (empresa_from_header.id if empresa_from_header else None)

    stmt = select(FELImportJob).order_by(FELImportJob.created_at.desc()).limit(limit)

    if scope.role_code != "superadmin":
        stmt = stmt.where(FELImportJob.tenant_id == scope.tenant_id)

    if empresa_id_final:
        stmt = stmt.where(FELImportJob.empresa_id == empresa_id_final)

    if estado:
        stmt = stmt.where(FELImportJob.estado == estado.upper())

    result = await db.execute(stmt)
    return result.scalars().all()


# ============================================================
# 2. Consultar estado de un Job FEL
# ============================================================
@router.get("/{job_id}", response_model=FELImportJobResponse)
async def get_fel_job_status(
    job_id: int,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
):
    """
    Consulta el estado actual de un job de importación FEL.
    Útil para polling desde el frontend (barra de progreso).
    """
    stmt = select(FELImportJob).where(FELImportJob.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(404, detail="Job no encontrado")

    if scope.role_code != "superadmin" and job.tenant_id != scope.tenant_id:
        raise HTTPException(403, detail="No autorizado")

    return job


# ============================================================
# 3. Cancelar Job FEL
# ============================================================
@router.post("/{job_id}/cancelar", response_model=FELImportJobResponse)
async def cancelar_fel_job(
    job_id: int,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
):
    """
    Cancela un job de importación FEL en estado PENDIENTE o PROCESANDO.
    El worker en background detectará el cambio y se detendrá.
    """
    stmt = select(FELImportJob).where(FELImportJob.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(404, detail="Job no encontrado")

    if scope.role_code != "superadmin" and job.tenant_id != scope.tenant_id:
        raise HTTPException(403, detail="No autorizado")

    if job.estado not in ("PENDIENTE", "PROCESANDO"):
        raise HTTPException(
            400,
            detail=(
                f"No se puede cancelar un job en estado '{job.estado}'. "
                "Solo se pueden cancelar jobs PENDIENTE o PROCESANDO."
            ),
        )

    job.estado = "CANCELADO"
    job.finalizado_en = datetime.now(timezone.utc)
    job.locked_at = None
    job.mensaje_error = "Cancelado por el usuario"
    await db.commit()
    await db.refresh(job)

    return job


# ============================================================
# 4. Re-procesar Job FEL
# ============================================================
@router.post(
    "/{job_id}/reprocesar",
    response_model=FELJobCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def reprocesar_fel_job(
    job_id: int,
    solo_errores: bool = Query(
        False, description="Si es True, solo reprocesa los XMLs que fallaron"
    ),
    background_tasks: BackgroundTasks = ...,
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
):
    """
    Crea un nuevo job a partir de un job anterior.
    - Si solo_errores=False: reprocesa todos los XMLs del ZIP original.
    - Si solo_errores=True: solo reprocesa los XMLs que tuvieron error.

    El ZIP original debe seguir disponible en disco (archivo_ruta).
    """
    stmt = select(FELImportJob).where(FELImportJob.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(404, detail="Job no encontrado")

    if scope.role_code != "superadmin" and job.tenant_id != scope.tenant_id:
        raise HTTPException(403, detail="No autorizado")

    if job.estado not in ("FALLIDO", "COMPLETADO", "CANCELADO"):
        raise HTTPException(
            400,
            detail=(
                f"No se puede reprocesar un job en estado '{job.estado}'. "
                "Solo se pueden reprocesar jobs FALLIDO, COMPLETADO o CANCELADO."
            ),
        )

    zip_path = Path(job.archivo_ruta)
    if not zip_path.exists():
        raise HTTPException(
            400,
            detail=(
                "El archivo ZIP original ya no está disponible en disco. "
                "Por favor, suba el archivo nuevamente."
            ),
        )

    schema_name = await _set_schema_for_query(db, scope)

    emp_nit_res = await db.execute(
        text("SELECT nit FROM empresas WHERE id = :eid"),
        {"eid": job.empresa_id},
    )
    empresa_nit = emp_nit_res.scalar_one().replace("-", "").strip()

    user_res = await db.execute(
        text("SELECT id, email, full_name FROM public.users WHERE id = :uid"),
        {"uid": scope.user_id},
    )
    user_data = user_res.first()
    if not user_data:
        raise HTTPException(404, detail="Usuario no encontrado")

    try:
        xml_files = []
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            for file_info in zip_ref.infolist():
                if not file_info.filename.lower().endswith(".xml"):
                    continue

                xml_bytes = zip_ref.read(file_info.filename)

                encoding = "utf-8"
                head = xml_bytes[:100].decode("utf-8", errors="ignore").lower()
                if 'encoding="' in head:
                    encoding = head.split('encoding="')[1].split('"')[0]

                try:
                    xml_text = xml_bytes.decode(encoding)
                except UnicodeDecodeError:
                    xml_text = xml_bytes.decode("utf-8", errors="replace")

                xml_files.append({
                    "filename": file_info.filename,
                    "xml_text": xml_text,
                    "raw_bytes": xml_bytes,
                })
    except Exception as e:
        raise HTTPException(500, detail=f"Error leyendo ZIP original: {str(e)}")

    if solo_errores and job.errores:
        archivos_con_error = {
            err.get("file", "")
            for err in job.errores
            if err.get("error") != "Duplicada (ya existe en el sistema)"
        }
        xml_files = [
            xf for xf in xml_files if xf["filename"] in archivos_con_error
        ]

        if not xml_files:
            raise HTTPException(
                400,
                detail=(
                    "No hay XMLs con error para reprocesar "
                    "(todos los errores fueron duplicadas)."
                ),
            )

    if not xml_files:
        raise HTTPException(400, detail="No se encontraron XMLs en el ZIP original")

    nuevo_job = FELImportJob(
        tenant_id=job.tenant_id,
        empresa_id=job.empresa_id,
        usuario_id=scope.user_id,
        archivo_original=f"reproceso_{job.archivo_original}",
        archivo_ruta=str(zip_path),
        formato="ZIP",
        tamano_bytes=job.tamano_bytes,
        archivos_totales=len(xml_files),
        estado="PENDIENTE",
    )
    db.add(nuevo_job)
    await db.commit()
    await db.refresh(nuevo_job)

    background_tasks.add_task(
        FELZipProcessor.process_job,
        job_id=nuevo_job.id,
        tenant_id=job.tenant_id,
        empresa_id=job.empresa_id,
        empresa_nit=empresa_nit,
        schema_name=schema_name,
        user_email=user_data.email,
        user_full_name=user_data.full_name,
        xml_files=xml_files,
    )

    return FELJobCreatedResponse(
        job_id=nuevo_job.id,
        public_id=nuevo_job.public_id,
        filename=nuevo_job.archivo_original,
        total_files=len(xml_files),
        estado=nuevo_job.estado,
        message=(
            f"Re-procesamiento programado: {len(xml_files)} XMLs "
            f"({'solo errores' if solo_errores else 'todos'})"
        ),
    )