"""
Procesador en background de ZIPs FEL.
Maneja la persistencia progresiva del job y notificación por email.
"""
import logging
from datetime import datetime, timezone
from decimal import Decimal

from app.core.email.service import email_service
from app.core.file_handlers import FileContent
from app.db.base import AsyncSessionLocal  # ✅ Import directo desde base
from app.models.global_models import FELImportJob
from app.services.facturas.contabilidad_service import clasificar_gasto_sat
from app.services.facturas.tipo_cambio_service import obtener_tipo_cambio
from app.services.fel.context import FelIngestionContext
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class FELZipProcessor:
    """
    Procesa un job de importación FEL en background.
    Crea su propia sesión de BD (no reutiliza la del request HTTP).
    """

    @staticmethod
    async def process_job(
        job_id: int,
        tenant_id: int,
        empresa_id: int,
        empresa_nit: str,
        schema_name: str,
        user_email: str,
        user_full_name: str,
        xml_files: list[dict],
    ):
        # ✅ Crear sesión independiente usando AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            job = await db.get(FELImportJob, job_id)
            if not job:
                logger.error(f"❌ Job {job_id} no encontrado")
                return

            # Marcar como procesando
            job.estado = "PROCESANDO"
            job.iniciado_en = datetime.now(timezone.utc)
            job.locked_at = datetime.now(timezone.utc)
            await db.commit()

            try:
                # Configurar search_path para acceder a tablas del tenant
                await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))

                facturas_creadas = 0
                facturas_duplicadas = 0
                errores = []

                for xml_data in xml_files:
                    try:
                        # ✅ VERIFICAR CANCELACIÓN antes de procesar cada XML
                        await db.refresh(job)
                        if job.estado == "CANCELADO":
                            logger.info(f"⏹️ Job {job_id} cancelado por el usuario")
                            job.finalizado_en = datetime.now(timezone.utc)
                            job.locked_at = None
                            job.mensaje_error = "Cancelado por el usuario"
                            await db.commit()

                            # Notificar cancelación
                            try:
                                await email_service.send_fel_import_cancelada(
                                    to=user_email,
                                    full_name=user_full_name,
                                    archivo_nombre=job.archivo_original,
                                    archivos_procesados=job.archivos_procesados,
                                    archivos_totales=job.archivos_totales,
                                )
                                job.notificado = True
                                job.notificado_en = datetime.now(timezone.utc)
                                await db.commit()
                            except Exception as email_err:
                                logger.error(f"Error enviando email de cancelación: {email_err}")

                            return

                        # 1. Construir FileContent para el XML individual
                        xml_content = FileContent(
                            raw_bytes=xml_data["raw_bytes"],
                            filename=xml_data["filename"],
                            mime_type="application/xml",
                            extension="xml",
                            parsed_data={"xml_text": xml_data["xml_text"]},
                        )

                        # 2. Parsear con FelIngestionContext (reutiliza XmlFelStrategy)
                        result = await FelIngestionContext.ingest(xml_content, db)

                        if not result.success:
                            errores.append({
                                "file": xml_data["filename"],
                                "error": result.error or "Error de parseo",
                            })
                            job.archivos_procesados += 1
                            job.porcentaje = int((job.archivos_procesados / job.archivos_totales) * 100)
                            await db.commit()
                            continue

                        datos = result.data

                        # 3. Validar duplicados
                        dup = await db.execute(
                            text("""
                                SELECT id FROM facturas_electronicas 
                                WHERE empresa_id = :e AND numero_autorizacion = :n
                            """),
                            {"e": empresa_id, "n": datos.get("numero_autorizacion")},
                        )

                        if dup.first():
                            facturas_duplicadas += 1
                            errores.append({
                                "file": xml_data["filename"],
                                "error": "Duplicada (ya existe en el sistema)",
                            })
                            job.archivos_procesados += 1
                            job.porcentaje = int((job.archivos_procesados / job.archivos_totales) * 100)
                            await db.commit()
                            continue

                        # 4. Determinar tipo de operación
                        em = datos.get("emisor_nit", "").replace("-", "")
                        rec = datos.get("receptor_nit", "").replace("-", "")

                        if em == empresa_nit:
                            tipo_op = "Venta"
                        elif rec == empresa_nit:
                            tipo_op = "Compra"
                        else:
                            errores.append({
                                "file": xml_data["filename"],
                                "error": "La empresa no participa en esta factura",
                            })
                            job.archivos_procesados += 1
                            job.porcentaje = int((job.archivos_procesados / job.archivos_totales) * 100)
                            await db.commit()
                            continue

                        # 5. Clasificación de gasto SAT
                        clasificacion_inicial = await clasificar_gasto_sat(datos)

                        # 6. Tipo de cambio
                        tc = Decimal("1.00000")
                        if datos.get("moneda") != "GTQ" and datos.get("fecha_emision"):
                            fecha = datos["fecha_emision"]
                            if hasattr(fecha, "date"):
                                fecha = fecha.date()
                            tc = await obtener_tipo_cambio(fecha, datos["moneda"], db) or tc

                        # 7. Crear factura en BD
                        await _crear_factura_background(
                            db, datos, empresa_id, tipo_op,
                            clasificacion_inicial, tc,
                            xml_data["filename"], xml_data["xml_text"],
                        )

                        facturas_creadas += 1

                    except Exception as e:
                        logger.error(f"Error procesando {xml_data['filename']}: {e}", exc_info=True)
                        errores.append({
                            "file": xml_data["filename"],
                            "error": str(e),
                        })

                    # Actualizar progreso (commit por cada archivo para no perder avance)
                    job.archivos_procesados += 1
                    job.facturas_creadas = facturas_creadas
                    job.facturas_duplicadas = facturas_duplicadas
                    job.facturas_con_error = len(errores)
                    job.errores = errores[:100]
                    job.porcentaje = int((job.archivos_procesados / job.archivos_totales) * 100)
                    await db.commit()

                # Completar job
                job.estado = "COMPLETADO"
                job.finalizado_en = datetime.now(timezone.utc)
                job.locked_at = None
                await db.commit()

                # Enviar email de éxito
                try:
                    await email_service.send_fel_import_completada(
                        to=user_email,
                        full_name=user_full_name,
                        archivo_nombre=job.archivo_original,
                        total_archivos=job.archivos_totales,
                        facturas_creadas=facturas_creadas,
                        facturas_duplicadas=facturas_duplicadas,
                        facturas_con_error=len(errores),
                    )
                    job.notificado = True
                    job.notificado_en = datetime.now(timezone.utc)
                    await db.commit()
                except Exception as e:
                    logger.error(f"Error enviando email de completado: {e}", exc_info=True)

                logger.info(
                    f"✅ Job {job_id} completado: "
                    f"{facturas_creadas} creadas, {facturas_duplicadas} duplicadas, "
                    f"{len(errores)} errores"
                )

            except Exception as e:
                logger.error(f"❌ Job {job_id} falló: {e}", exc_info=True)
                job.estado = "FALLIDO"
                job.mensaje_error = str(e)[:1000]
                job.finalizado_en = datetime.now(timezone.utc)
                job.locked_at = None
                await db.commit()

                # Enviar email de fallo
                try:
                    await email_service.send_fel_import_fallida(
                        to=user_email,
                        full_name=user_full_name,
                        archivo_nombre=job.archivo_original,
                        error_mensaje=str(e)[:500],
                    )
                    job.notificado = True
                    job.notificado_en = datetime.now(timezone.utc)
                    await db.commit()
                except Exception as email_err:
                    logger.error(f"Error enviando email de fallo: {email_err}", exc_info=True)


async def _crear_factura_background(
    db: AsyncSession,
    datos: dict,
    empresa_id: int,
    tipo_op: str,
    clasificacion: str,
    tc: Decimal,
    filename: str,
    xml_text: str,
):
    """
    Crea la factura en BD (versión para background, sin depender del endpoint).
    """
    from app.models.tenant_models import FacturaDetalle, FacturaElectronica

    items = datos.pop("items", [])
    tc_float = float(tc)

    factura = FacturaElectronica(
        empresa_id=empresa_id,
        xml_original=xml_text,
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