# app/api/v1/endpoints/facturas.py
import logging
import tempfile
import zipfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import List

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
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.file_handlers import FileHandlerRegistry
from app.core.security import DataScope, get_data_scope
from app.db.session import get_public_db
from app.dependencies.empresa import get_active_empresa
from app.models.global_models import FELImportJob
from app.models.tenant_models import Empresa, FacturaElectronica
from app.schemas.contabilidad.partida import DetallePartidaOut, PartidaOut
from app.schemas.fel.factura import FacturaOut
from app.schemas.fel.job import FELImportJobResponse, FELJobCreatedResponse
from app.services.facturas.contabilidad_service import (
    clasificar_gasto_sat,
    generar_partida_desde_factura,
)
from app.services.facturas.tipo_cambio_service import obtener_tipo_cambio
from app.services.fel.context import FelIngestionContext
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
# 1. Upload de Facturas (soporta XML, PDF y ZIP)
# ============================================================
@router.post("/upload", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_facturas(
    background_tasks: BackgroundTasks,
    empresa_id: int | None = Query(None),
    tenant_id: int | None = Query(None),
    files: List[UploadFile] = File(...),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
    empresa_from_header: Empresa | None = Depends(get_active_empresa),
):
    """
    Upload de facturas FEL. Soporta:
    - XML individuales (procesamiento síncrono)
    - PDF con XML embebido o texto (procesamiento síncrono)
    - ZIP con múltiples XMLs del SAT (procesamiento asíncrono en background)
    """
    schema_name = await _set_schema_for_query(db, scope, tenant_id)
    empresa_id_final = empresa_id or (empresa_from_header.id if empresa_from_header else None)
    if not empresa_id_final:
        raise HTTPException(400, detail="Debe especificar una empresa")

    # Validar empresa y obtener NIT
    emp_nit_res = await db.execute(
        text("SELECT nit FROM empresas WHERE id = :eid"),
        {"eid": empresa_id_final},
    )
    empresa_nit = emp_nit_res.scalar_one().replace("-", "").strip()

    # Obtener info del usuario para notificación
    user_res = await db.execute(
        text("SELECT id, email, full_name FROM public.users WHERE id = :uid"),
        {"uid": scope.user_id},
    )
    user_data = user_res.first()
    if not user_data:
        raise HTTPException(404, detail="Usuario no encontrado")

    # Separar ZIPs de archivos regulares
    zip_files = [f for f in files if f.filename and f.filename.lower().endswith(".zip")]
    regular_files = [
        f for f in files if not (f.filename and f.filename.lower().endswith(".zip"))
    ]

    facturas_creadas = []
    rechazos = []
    jobs_creados: list[FELJobCreatedResponse] = []

    # ============================================================
    # Procesar ZIPs en background
    # ============================================================
    for zip_file in zip_files:
        try:
            # 1. Leer ZIP con el handler registrado
            handler = FileHandlerRegistry.resolve(zip_file.filename, zip_file.content_type)
            content = await handler.read(zip_file)

            xml_files = content.parsed_data.get("xml_files", [])
            if not xml_files:
                rechazos.append(f"{zip_file.filename}: El ZIP no contiene archivos XML")
                continue

            # 2. Guardar archivo temporalmente (para auditoría/re-procesamiento)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
                tmp.write(content.raw_bytes)
                tmp_path = tmp.name

            # 3. Crear job en BD
            job = FELImportJob(
                tenant_id=scope.tenant_id,
                empresa_id=empresa_id_final,
                usuario_id=scope.user_id,
                archivo_original=zip_file.filename,
                archivo_ruta=tmp_path,
                formato="ZIP",
                tamano_bytes=len(content.raw_bytes),
                archivos_totales=len(xml_files),
                estado="PENDIENTE",
            )
            db.add(job)
            await db.commit()
            await db.refresh(job)

            # 4. Programar procesamiento en background
            background_tasks.add_task(
                FELZipProcessor.process_job,
                job_id=job.id,
                tenant_id=scope.tenant_id,
                empresa_id=empresa_id_final,
                empresa_nit=empresa_nit,
                schema_name=schema_name,
                user_email=user_data.email,
                user_full_name=user_data.full_name,
                xml_files=xml_files,
            )

            jobs_creados.append(FELJobCreatedResponse(
                job_id=job.id,
                public_id=job.public_id,
                filename=zip_file.filename,
                total_files=len(xml_files),
                estado=job.estado,
                message=f"ZIP en cola de procesamiento: {len(xml_files)} XMLs detectados",
            ))

        except Exception as e:
            logger.error(f"Error preparando ZIP {zip_file.filename}: {e}", exc_info=True)
            rechazos.append(f"{zip_file.filename}: {str(e)}")

    # ============================================================
    # Procesar archivos regulares (XML, PDF) de forma síncrona
    # ============================================================
    for file in regular_files:
        try:
            handler = FileHandlerRegistry.resolve(file.filename, file.content_type)
            content = await handler.read(file)
            result = await FelIngestionContext.ingest(content, db)

            if not result.success:
                rechazos.append(f"{file.filename}: {result.error}")
                continue

            datos = result.data

            # Validar duplicados
            dup = await db.execute(
                text("""
                    SELECT id FROM facturas_electronicas 
                    WHERE empresa_id = :e AND numero_autorizacion = :n
                """),
                {"e": empresa_id_final, "n": datos.get("numero_autorizacion")},
            )
            if dup.first():
                rechazos.append(f"{file.filename}: Duplicada")
                continue

            # Determinar tipo de operación
            em = datos.get("emisor_nit", "").replace("-", "")
            rec = datos.get("receptor_nit", "").replace("-", "")
            if em == empresa_nit:
                tipo_op = "Venta"
            elif rec == empresa_nit:
                tipo_op = "Compra"
            else:
                rechazos.append(f"{file.filename}: Empresa no participa")
                continue

            # Clasificación de gasto
            clasificacion_inicial = await clasificar_gasto_sat(datos)

            # Tipo de cambio
            tc = Decimal("1.00000")
            if datos.get("moneda") != "GTQ" and datos.get("fecha_emision"):
                tc = await obtener_tipo_cambio(
                    datos["fecha_emision"].date(), datos["moneda"], db
                ) or tc

            # Crear factura
            factura = await _crear_factura_en_bd(
                db, datos, empresa_id_final, tipo_op,
                clasificacion_inicial, tc, file.filename, content,
            )
            facturas_creadas.append(factura)

        except Exception as e:
            logger.error(f"Error en {file.filename}: {e}", exc_info=True)
            rechazos.append(f"{file.filename}: {str(e)}")

    await db.commit()

    response = {
        "cargadas": len(facturas_creadas),
        "rechazadas": rechazos,
    }

    if jobs_creados:
        response["jobs_background"] = [j.model_dump(mode="json") for j in jobs_creados]

    return response


# ============================================================
# 2. Consultar estado de un Job FEL
# ============================================================
@router.get("/jobs/{job_id}", response_model=FELImportJobResponse)
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

    # Validar que el job pertenezca al tenant del usuario
    if scope.role_code != "superadmin" and job.tenant_id != scope.tenant_id:
        raise HTTPException(403, detail="No autorizado")

    return job


# ============================================================
# 3. Listar jobs recientes del tenant/empresa
# ============================================================
@router.get("/jobs", response_model=List[FELImportJobResponse])
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
# 4. Cancelar Job FEL
# ============================================================
@router.post("/jobs/{job_id}/cancelar", response_model=FELImportJobResponse)
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

    # Validar tenant
    if scope.role_code != "superadmin" and job.tenant_id != scope.tenant_id:
        raise HTTPException(403, detail="No autorizado")

    # Validar estado: solo se puede cancelar si está pendiente o procesando
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
# 5. Re-procesar Job FEL (fallido, completado con errores o cancelado)
# ============================================================
@router.post(
    "/jobs/{job_id}/reprocesar",
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

    # Validar tenant
    if scope.role_code != "superadmin" and job.tenant_id != scope.tenant_id:
        raise HTTPException(403, detail="No autorizado")

    # Validar estado: solo se puede reprocesar si falló, se completó o se canceló
    if job.estado not in ("FALLIDO", "COMPLETADO", "CANCELADO"):
        raise HTTPException(
            400,
            detail=(
                f"No se puede reprocesar un job en estado '{job.estado}'. "
                "Solo se pueden reprocesar jobs FALLIDO, COMPLETADO o CANCELADO."
            ),
        )

    # Validar que el ZIP original exista en disco
    zip_path = Path(job.archivo_ruta)
    if not zip_path.exists():
        raise HTTPException(
            400,
            detail=(
                "El archivo ZIP original ya no está disponible en disco. "
                "Por favor, suba el archivo nuevamente."
            ),
        )

    # Configurar search_path
    schema_name = await _set_schema_for_query(db, scope)

    # Obtener NIT de la empresa
    emp_nit_res = await db.execute(
        text("SELECT nit FROM empresas WHERE id = :eid"),
        {"eid": job.empresa_id},
    )
    empresa_nit = emp_nit_res.scalar_one().replace("-", "").strip()

    # Obtener info del usuario
    user_res = await db.execute(
        text("SELECT id, email, full_name FROM public.users WHERE id = :uid"),
        {"uid": scope.user_id},
    )
    user_data = user_res.first()
    if not user_data:
        raise HTTPException(404, detail="Usuario no encontrado")

    # Extraer XMLs del ZIP original
    try:
        xml_files = []
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            for file_info in zip_ref.infolist():
                if not file_info.filename.lower().endswith(".xml"):
                    continue

                xml_bytes = zip_ref.read(file_info.filename)

                # Detectar encoding
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

    # Filtrar solo errores si se solicita
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

    # Crear NUEVO job (no reutilizamos el anterior para mantener historial)
    nuevo_job = FELImportJob(
        tenant_id=job.tenant_id,
        empresa_id=job.empresa_id,
        usuario_id=scope.user_id,
        archivo_original=f"reproceso_{job.archivo_original}",
        archivo_ruta=str(zip_path),  # Reutiliza la misma ruta
        formato="ZIP",
        tamano_bytes=job.tamano_bytes,
        archivos_totales=len(xml_files),
        estado="PENDIENTE",
    )
    db.add(nuevo_job)
    await db.commit()
    await db.refresh(nuevo_job)

    # Programar en background
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


# ============================================================
# 6. Generar Partida desde Factura (DELEGADO AL SERVICIO)
# ============================================================
@router.post(
    "/{factura_id}/generar-partida",
    response_model=PartidaOut,
    status_code=status.HTTP_201_CREATED,
)
async def generar_partida_desde_factura_endpoint(
    factura_id: int,
    empresa_id: int | None = Query(None),
    tenant_id: int | None = Query(None),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
    empresa_from_header: Empresa | None = Depends(get_active_empresa),
):
    schema_name = await _set_schema_for_query(db, scope, tenant_id)
    empresa_id_final = empresa_id or (empresa_from_header.id if empresa_from_header else None)
    if not empresa_id_final:
        raise HTTPException(400, detail="Debe especificar una empresa")

    stmt = select(FacturaElectronica).where(
        FacturaElectronica.id == factura_id,
        FacturaElectronica.empresa_id == empresa_id_final,
    )
    result = await db.execute(stmt)
    factura = result.scalar_one_or_none()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    try:
        partida = await generar_partida_desde_factura(
            db=db,
            factura=factura,
            empresa_id=empresa_id_final,
            schema_name=schema_name,
        )
        await db.commit()
        await db.refresh(partida, ["detalles"])
        return PartidaOut(
            id=partida.id,
            numero_poliza=partida.numero_poliza,
            fecha=partida.fecha,
            descripcion=partida.descripcion,
            empresa_nombre="",
            created_at=partida.created_at,
            detalles=[
                DetallePartidaOut(
                    id=d.id,
                    cuenta_id=d.cuenta_id,
                    cuenta_codigo=d.cuenta.codigo if d.cuenta else "",
                    cuenta_nombre=d.cuenta.nombre if d.cuenta else "",
                    tipo_movimiento=d.tipo_movimiento,
                    monto=d.monto,
                )
                for d in partida.detalles
            ],
        )
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error(f"Error generando partida: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ============================================================
# 7. Listar facturas
# ============================================================
@router.get("/", response_model=List[FacturaOut])
async def listar_facturas(
    empresa_id: int | None = Query(None),
    tenant_id: int | None = Query(None),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
    empresa_from_header: Empresa | None = Depends(get_active_empresa),
):
    empresa_id_final = empresa_id or (empresa_from_header.id if empresa_from_header else None)
    stmt = (
        select(FacturaElectronica)
        .options(selectinload(FacturaElectronica.detalles))
        .order_by(FacturaElectronica.fecha_emision.desc())
    )
    if empresa_id_final:
        stmt = stmt.where(FacturaElectronica.empresa_id == empresa_id_final)
    result = await db.execute(stmt)
    return [FacturaOut.model_validate(f) for f in result.scalars().all()]


# ============================================================
# Helper privado: Crear factura en BD (flujo síncrono)
# ============================================================
async def _crear_factura_en_bd(db, datos, empresa_id, tipo_op, clasificacion, tc, filename, content):
    """Helper para persistir la factura (flujo síncrono del endpoint)."""
    from app.models.tenant_models import FacturaDetalle

    xml_original = content.parsed_data.get("xml_text", "") if content.parsed_data else None
    items = datos.pop("items", [])
    tc_float = float(tc)

    factura = FacturaElectronica(
        empresa_id=empresa_id,
        xml_original=xml_original,
        numero_autorizacion=datos["numero_autorizacion"],
        serie=datos.get("serie"),
        numero=datos.get("numero"),
        fecha_emision=datos["fecha_emision"],
        emisor_nit=datos["emisor_nit"],
        emisor_nombre=datos["emisor_nombre"],
        receptor_nit=datos["receptor_nit"],
        receptor_nombre=datos["receptor_nombre"],
        total_gravado=datos["total_gravado"],
        total_iva=datos["total_iva"],
        total_exento=datos.get("total_exento", 0),
        total=datos["total"],
        tipo_cambio=tc,
        total_gravado_gtq=float(datos["total_gravado"]) * tc_float,
        total_iva_gtq=float(datos["total_iva"]) * tc_float,
        total_exento_gtq=float(datos.get("total_exento", 0)) * tc_float,
        total_gtq=float(datos["total"]) * tc_float,
        es_exportacion=datos.get("es_exportacion", False),
        tipo_operacion=tipo_op,
        estado="Activa",
        tipo_documento=datos.get("tipo_documento"),
        moneda=datos.get("moneda"),
        xml_filename=filename,
        clasificacion_gasto_sat=clasificacion,
    )
    db.add(factura)
    await db.flush()

    for it in items:
        db.add(FacturaDetalle(
            factura_id=factura.id,
            cantidad=it["cantidad"],
            descripcion=it["descripcion"],
            precio_unitario=it["precio_unitario"],
            total_linea=it["total_linea"],
            iva_linea=it.get("iva_linea", 0),
            precio_unitario_gtq=float(it["precio_unitario"]) * tc_float,
            total_linea_gtq=float(it["total_linea"]) * tc_float,
            iva_linea_gtq=float(it.get("iva_linea", 0)) * tc_float,
            bien_o_servicio=it.get("bien_o_servicio", "B"),
        ))

    return factura