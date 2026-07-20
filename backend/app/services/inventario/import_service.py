"""
Servicio para importar inventarios con procesamiento asíncrono por chunks.

Flujo:
1. guardar_archivo() → guarda en disco, crea job (PENDIENTE), retorna job
2. procesar_job() → ejecutado en BackgroundTask, procesa por chunks
3. consultar_estado() → endpoint para polling del frontend
"""
import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import pandas as pd
from app.models.global_models import InventarioImportacionJob, User
from app.models.tenant_models import (
    InventarioBodega,
    InventarioImportacion,
    InventarioItem,
    InventarioProducto,
    InventarioToma,
)
from app.services.inventario.item_service import ItemService
from sqlalchemy import and_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Directorio temporal para archivos (configurable vía settings)
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/tmp/fastconta/uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Tamaño del batch de procesamiento
BATCH_SIZE = int(os.getenv("IMPORT_BATCH_SIZE", "500"))

COLUMNAS_ESPERADAS = {
    "codigo": ["codigo", "código", "cod", "sku"],
    "descripcion": ["descripcion", "descripción", "desc", "producto", "nombre"],
    "costo_unitario": ["costo", "costo_unitario", "costo unitario", "pu", "precio"],
    "unidad_medida": ["unidad", "unidad_medida", "um", "u/m"],
    "bodega": ["bodega", "bod", "almacen", "almacén"],
    "cantidad": ["cantidad", "cant", "qty", "existencia", "stock"],
}


class ImportService:
    """
    Servicio para importar inventarios con procesamiento asíncrono por chunks.
    
    El job se crea en schema public (global) para monitoreo centralizado,
    pero los datos se procesan en el schema del tenant.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.item_service = ItemService(db)

    # ============================================================
    # PASO 1: Guardar archivo y crear job (rápido, <1s)
    # ============================================================

    async def guardar_archivo(
        self,
        toma: InventarioToma,
        file_content: bytes,
        filename: str,
        usuario_id: int,
        tenant_schema: str,
        modo: str = "REEMPLAZAR",
    ) -> InventarioImportacionJob:
        """
        Guarda el archivo en disco y crea un job en BD global.
        NO procesa el archivo → eso lo hace procesar_job() en background.
        """
        if toma.estado != "BORRADOR":
            raise ValueError("Solo se puede importar en tomas en estado BORRADOR")
        if modo not in ("REEMPLAZAR", "AGREGAR"):
            raise ValueError("Modo debe ser REEMPLAZAR o AGREGAR")

        # Validar extensión
        ext = Path(filename).suffix.lower()
        if ext not in (".xlsx", ".xls", ".csv"):
            raise ValueError("Formato no soportado. Use .xlsx, .xls o .csv")

        # Generar nombre único para evitar colisiones
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        ruta_archivo = UPLOAD_DIR / unique_name

        # Guardar en disco (I/O síncrono, ejecutado en thread pool)
        await asyncio.to_thread(self._write_file, ruta_archivo, file_content)

        # Crear job en schema public (global)
        job = InventarioImportacionJob(
            tenant_id=toma.tenant_id,
            empresa_id=toma.empresa_id,
            toma_id=toma.id,
            usuario_id=usuario_id,
            archivo_original=filename,
            archivo_ruta=str(ruta_archivo),
            formato=ext.lstrip("."),
            tamano_bytes=len(file_content),
            modo=modo,
            estado="PENDIENTE",
            tenant_schema=tenant_schema,
            created_by=usuario_id,
            updated_by=usuario_id,
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)

        return job

    @staticmethod
    def _write_file(ruta: Path, content: bytes) -> None:
        """Escribe archivo en disco (ejecutado en thread pool)."""
        with open(ruta, "wb") as f:
            f.write(content)

    # ============================================================
    # PASO 2: Procesar job en background (lento, por chunks)
    # ============================================================

    async def procesar_job(self, job_id: int) -> None:
        """
        Procesa un job por chunks. Diseñado para ejecutarse en BackgroundTask.
        
        Crea su propia sesión de BD (BackgroundTask corre fuera del request scope).
        """
        from app.db.base import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            try:
                await self._procesar_job_interno(db, job_id)
            except Exception as e:
                logger.exception(f"Error fatal procesando job {job_id}: {e}")
                await self._marcar_fallido(db, job_id, str(e))

    async def _procesar_job_interno(self, db: AsyncSession, job_id: int) -> None:
        """Lógica interna de procesamiento."""
        # Cargar job
        job = await db.get(InventarioImportacionJob, job_id)
        if not job:
            logger.error(f"Job {job_id} no encontrado")
            return

        # Lock para evitar ejecución duplicada
        if job.locked_at is not None:
            logger.warning(f"Job {job_id} ya está siendo procesado")
            return

        job.locked_at = datetime.now(timezone.utc)
        job.estado = "PROCESANDO"
        job.iniciado_en = job.locked_at
        await db.commit()

        try:
            # 1. Cambiar search_path al schema del tenant
            await db.execute(
                text(f"SET LOCAL search_path TO {job.tenant_schema}, public")
            )

            # 2. Verificar que la toma aún existe
            toma = await db.get(InventarioToma, job.toma_id)
            if not toma:
                job.estado = "TOMA_ELIMINADA"
                job.mensaje_error = "La toma de inventario fue eliminada"
                job.finalizado_en = datetime.now(timezone.utc)
                await db.commit()
                return

            if toma.estado != "BORRADOR":
                job.estado = "FALLIDO"
                job.mensaje_error = (
                    f"La toma ya no está en estado BORRADOR (estado actual: {toma.estado})"
                )
                job.finalizado_en = datetime.now(timezone.utc)
                await db.commit()
                return

            # 3. Leer archivo y contar filas totales
            archivo_ruta = Path(job.archivo_ruta)
            if not archivo_ruta.exists():
                raise FileNotFoundError(f"Archivo no encontrado: {archivo_ruta}")

            total_filas, mapa_columnas = await self._contar_filas(
                archivo_ruta, job.formato
            )
            job.filas_totales = total_filas
            await db.commit()

            # 4. Pre-cargar catálogos (bodegas y productos)
            bodegas_map, productos_map = await self._cargar_catalogos(
                db, job.tenant_id, job.empresa_id
            )

            # 5. Si modo REEMPLAZAR, borrar items existentes
            if job.modo == "REEMPLAZAR":
                stmt_delete = InventarioItem.__table__.delete().where(
                    InventarioItem.toma_id == job.toma_id
                )
                await db.execute(stmt_delete)
                await db.commit()

            # 6. Procesar por chunks
            item_service = ItemService(db)
            todas_errores: list[dict] = []
            total_validas = 0
            total_errores = 0
            batch_items: list[InventarioItem] = []

            async for chunk_df in self._leer_chunks(
                archivo_ruta, job.formato, BATCH_SIZE
            ):
                items_validos, errores_chunk = self._validar_chunk(
                    chunk_df, mapa_columnas
                )

                # Crear items en batch
                for item_data in items_validos:
                    prod = (
                        productos_map.get(item_data["codigo"])
                        if item_data["codigo"]
                        else None
                    )
                    bod = (
                        bodegas_map.get(item_data["bodega_codigo"])
                        if item_data["bodega_codigo"]
                        else None
                    )

                    batch_items.append(
                        InventarioItem(
                            toma_id=job.toma_id,
                            producto_id=prod.id if prod else None,
                            bodega_id=bod.id if bod else None,
                            created_by=job.usuario_id,
                            updated_by=job.usuario_id,
                            **item_data,
                        )
                    )

                # Flush batch cada BATCH_SIZE items
                if len(batch_items) >= BATCH_SIZE:
                    db.add_all(batch_items)
                    await db.flush()
                    batch_items.clear()

                total_validas += len(items_validos)
                total_errores += len(errores_chunk)
                todas_errores.extend(errores_chunk)

                # Actualizar progreso
                job.filas_procesadas += len(chunk_df)
                job.filas_validas = total_validas
                job.filas_con_error = total_errores
                job.porcentaje = int(
                    (job.filas_procesadas / max(job.filas_totales, 1)) * 100
                )
                await db.commit()

            # 7. Insertar items restantes
            if batch_items:
                db.add_all(batch_items)
                await db.flush()

            # 8. Recalcular totales de la toma
            await item_service.recalcular_totales_por_toma_id(db, job.toma_id)

            # 9. Crear registro de importación (auditoría en schema tenant)
            importacion = InventarioImportacion(
                toma_id=job.toma_id,
                archivo_original=job.archivo_original,
                formato=job.formato,
                modo=job.modo,
                filas_procesadas=job.filas_procesadas,
                filas_validas=total_validas,
                filas_con_error=total_errores,
                errores=todas_errores[:1000] or None,  # limitar tamaño JSONB
                created_by=job.usuario_id,
                updated_by=job.usuario_id,
            )
            db.add(importacion)
            await db.flush()

            # 10. Marcar job como completado
            job.estado = "COMPLETADO"
            job.importacion_id = importacion.id
            job.finalizado_en = datetime.now(timezone.utc)
            job.porcentaje = 100
            await db.commit()

            logger.info(
                f"Job {job.public_id} completado: "
                f"{total_validas} válidas, {total_errores} errores"
            )

            # 11. Enviar notificación por email (no bloqueante)
            try:
                await self._enviar_notificacion(db, job, importacion)
            except Exception as e:
                logger.warning(
                    f"No se pudo enviar notificación del job {job_id}: {e}"
                )

            # 12. Limpiar archivo temporal
            try:
                archivo_ruta.unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"No se pudo eliminar archivo temporal: {e}")

        except Exception as e:
            await self._marcar_fallido(db, job_id, str(e))
            raise

    async def _marcar_fallido(
        self, db: AsyncSession, job_id: int, mensaje: str
    ) -> None:
        """Marca un job como fallido."""
        job = await db.get(InventarioImportacionJob, job_id)
        if job:
            job.estado = "FALLIDO"
            job.mensaje_error = mensaje[:2000]  # limitar tamaño
            job.finalizado_en = datetime.now(timezone.utc)
            await db.commit()

            # Intentar notificar el fallo
            try:
                await self._enviar_notificacion(db, job, None)
            except Exception:
                pass

    # ============================================================
    # PASO 3: Lectura por chunks
    # ============================================================

    async def _contar_filas(
        self, ruta: Path, formato: str
    ) -> tuple[int, dict[str, str]]:
        """Cuenta filas totales y mapea columnas (primera pasada rápida)."""
        def _leer() -> pd.DataFrame:
            if formato in ("xlsx", "xls"):
                # read_only=True es mucho más rápido y consume menos memoria
                df = pd.read_excel(ruta, dtype=str, read_only=True)
            else:
                df = pd.read_csv(ruta, dtype=str, encoding="utf-8-sig")
            df.columns = [str(c).strip() for c in df.columns]
            return df.dropna(how="all")

        df = await asyncio.to_thread(_leer)
        return len(df), self._normalizar_columnas(df)

    async def _leer_chunks(
        self, ruta: Path, formato: str, chunk_size: int
    ):
        """Generador asíncrono que produce DataFrames de chunk_size filas."""
        def _leer_chunk_csv():
            return pd.read_csv(
                ruta, dtype=str, encoding="utf-8-sig", chunksize=chunk_size
            )

        def _leer_chunk_excel() -> pd.DataFrame:
            df = pd.read_excel(ruta, dtype=str, read_only=True)
            df.columns = [str(c).strip() for c in df.columns]
            return df.dropna(how="all")

        if formato == "csv":
            reader = await asyncio.to_thread(_leer_chunk_csv)
            for chunk in reader:
                chunk.columns = [str(c).strip() for c in chunk.columns]
                yield chunk.dropna(how="all")
        else:
            # Excel: cargar una vez, iterar por slices
            df = await asyncio.to_thread(_leer_chunk_excel)
            for start in range(0, len(df), chunk_size):
                yield df.iloc[start : start + chunk_size].copy()

    @staticmethod
    def _normalizar_columnas(df: pd.DataFrame) -> dict[str, str]:
        """Mapea nombres de columnas del archivo a nombres canónicos."""
        mapa: dict[str, str] = {}
        cols_lower = {c.lower().strip(): c for c in df.columns}
        for canonico, aliases in COLUMNAS_ESPERADAS.items():
            for alias in aliases:
                if alias in cols_lower:
                    mapa[canonico] = cols_lower[alias]
                    break
        requeridas = {"descripcion", "costo_unitario", "cantidad"}
        faltantes = requeridas - set(mapa.keys())
        if faltantes:
            raise ValueError(
                f"Columnas obligatorias faltantes: {sorted(faltantes)}. "
                f"Columnas detectadas: {list(df.columns)}"
            )
        return mapa

    @staticmethod
    def _validar_chunk(
        df: pd.DataFrame, mapa: dict[str, str]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Valida un chunk y retorna (items_validos, errores)."""
        items_validos: list[dict[str, Any]] = []
        errores: list[dict[str, Any]] = []

        for idx, row in df.iterrows():
            try:
                descripcion = str(
                    row.get(mapa.get("descripcion", ""), "")
                ).strip()
                if not descripcion:
                    raise ValueError("Descripción vacía")

                costo_raw = str(row[mapa["costo_unitario"]]).strip()
                costo_raw = (
                    costo_raw.replace(",", "").replace("Q", "").replace(" ", "")
                )
                try:
                    costo = Decimal(costo_raw)
                    if costo < 0:
                        raise ValueError("Costo unitario negativo")
                except (InvalidOperation, ValueError):
                    raise ValueError(f"Costo unitario inválido: '{costo_raw}'")

                cant_raw = str(row[mapa["cantidad"]]).strip()
                cant_raw = cant_raw.replace(",", "").replace(" ", "")
                try:
                    cantidad = Decimal(cant_raw)
                    if cantidad < 0:
                        raise ValueError("Cantidad negativa")
                except (InvalidOperation, ValueError):
                    raise ValueError(f"Cantidad inválida: '{cant_raw}'")

                codigo = ImportService._limpiar_valor(
                    row.get(mapa.get("codigo", ""), None)
                )
                unidad = ImportService._limpiar_valor(
                    row.get(mapa.get("unidad_medida", ""), "UND"),
                    default="UND",
                )
                bodega = ImportService._limpiar_valor(
                    row.get(mapa.get("bodega", ""), None)
                )

                items_validos.append({
                    "codigo": codigo,
                    "descripcion": descripcion,
                    "costo_unitario": costo,
                    "unidad_medida": unidad,
                    "bodega_codigo": bodega,
                    "cantidad": cantidad,
                    "costo_total": (cantidad * costo).quantize(Decimal("0.01")),
                })
            except Exception as e:
                errores.append({"fila": int(idx) + 2, "mensaje": str(e)})

        return items_validos, errores

    @staticmethod
    def _limpiar_valor(valor: Any, default: str | None = None) -> str | None:
        """Convierte valores NaN/None a None o al default especificado."""
        if valor is None:
            return default
        s = str(valor).strip()
        if not s or s.lower() in ("nan", "none", ""):
            return default
        return s

    # ============================================================
    # Helpers
    # ============================================================

    async def _cargar_catalogos(
        self, db: AsyncSession, tenant_id: int, empresa_id: int
    ) -> tuple[dict[str, InventarioBodega], dict[str, InventarioProducto]]:
        """Pre-carga bodegas y productos para evitar N+1."""
        stmt_b = select(InventarioBodega).where(
            and_(
                InventarioBodega.tenant_id == tenant_id,
                InventarioBodega.empresa_id == empresa_id,
                InventarioBodega.is_active.is_(True),
            )
        )
        result_b = await db.execute(stmt_b)
        bodegas_map = {
            b.codigo: b for b in result_b.scalars().all() if b.codigo
        }

        stmt_p = select(InventarioProducto).where(
            and_(
                InventarioProducto.tenant_id == tenant_id,
                InventarioProducto.empresa_id == empresa_id,
                InventarioProducto.codigo.isnot(None),
            )
        )
        result_p = await db.execute(stmt_p)
        productos_map = {
            p.codigo: p for p in result_p.scalars().all() if p.codigo
        }

        return bodegas_map, productos_map

    async def _enviar_notificacion(
        self,
        db: AsyncSession,
        job: InventarioImportacionJob,
        importacion: InventarioImportacion | None,
    ) -> None:
        """Envía email al usuario con el resultado de la importación."""
        # Cargar usuario
        usuario = await db.get(User, job.usuario_id)
        if not usuario or not usuario.email:
            return

        # Cargar toma para contexto (necesita cambiar search_path)
        await db.execute(
            text(f"SET LOCAL search_path TO {job.tenant_schema}, public")
        )
        toma = await db.get(InventarioToma, job.toma_id)

        periodo = "N/A"
        if toma:
            periodo = f"{toma.anio_periodo}/{str(toma.mes_periodo).zfill(2)}"

        # ✅ Usar el EmailService existente
        from app.core.email.service import email_service

        if job.estado == "COMPLETADO":
            await email_service.send_importacion_completada(
                to=usuario.email,
                full_name=usuario.full_name or usuario.email,
                archivo_nombre=job.archivo_original,
                periodo=periodo,
                modo=job.modo,
                filas_procesadas=job.filas_procesadas,
                filas_validas=job.filas_validas,
                filas_con_error=job.filas_con_error,
            )
        else:
            await email_service.send_importacion_fallida(
                to=usuario.email,
                full_name=usuario.full_name or usuario.email,
                archivo_nombre=job.archivo_original,
                error_mensaje=job.mensaje_error or "Error desconocido",
            )

        job.notificado = True
        job.notificado_en = datetime.now(timezone.utc)
        await db.commit()

    # ============================================================
    # Consulta de estado (para polling del frontend)
    # ============================================================

    async def consultar_estado(
        self, job_public_id: str
    ) -> InventarioImportacionJob | None:
        """Consulta el estado actual de un job (global, sin filtro tenant)."""
        stmt = select(InventarioImportacionJob).where(
            InventarioImportacionJob.public_id == job_public_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def listar_jobs_usuario(
        self, usuario_id: int, tenant_id: int, limit: int = 20
    ) -> list[InventarioImportacionJob]:
        """Lista los jobs recientes de un usuario en un tenant."""
        stmt = (
            select(InventarioImportacionJob)
            .where(
                and_(
                    InventarioImportacionJob.tenant_id == tenant_id,
                    InventarioImportacionJob.usuario_id == usuario_id,
                )
            )
            .order_by(InventarioImportacionJob.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def listar_jobs_toma(
        self, toma_id: int, tenant_id: int
    ) -> list[InventarioImportacionJob]:
        """Lista todos los jobs de una toma específica."""
        stmt = (
            select(InventarioImportacionJob)
            .where(
                and_(
                    InventarioImportacionJob.tenant_id == tenant_id,
                    InventarioImportacionJob.toma_id == toma_id,
                )
            )
            .order_by(InventarioImportacionJob.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())