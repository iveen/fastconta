"""
Script de backfill para clasificar facturas existentes.

Características:
  - Soporte multi-tenant: itera todos los schemas de tenant
  - Opción --tenant: procesa solo un schema específico
  - Opción --solo-no-clasificadas: solo procesa facturas con todos los booleanos en False
  - Opción --limit: máximo de facturas por tenant
  - Opción --dry-run: preview sin aplicar cambios
  - Filtra campos derivados (no existentes en el modelo)
  - Manejo de errores por tenant sin detener el proceso

Uso:
  python -m app.scripts.backfill_clasificacion_facturas
  python -m app.scripts.backfill_clasificacion_facturas --tenant tenant_abc --dry-run
  python -m app.scripts.backfill_clasificacion_facturas --solo-no-clasificadas --limit 100
"""

import argparse
import asyncio
import logging
import os
import sys

from sqlalchemy import and_, func, select, text
from sqlalchemy.orm import selectinload

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import AsyncSessionLocal
from app.models.tenant_models import FacturaElectronica, FacturaImpuestoEspecial
from app.services.fel.clasificador_facturas import clasificar_factura

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Campos que el clasificador retorna pero NO están en el modelo (solo informativos)
CAMPOS_DERIVADOS = {"clasificacion_gasto_sat_derived"}

# Campos booleanos que usamos para detectar facturas "no clasificadas"
CAMPOS_BOOLEANOS_CLASIFICACION = [
    "es_medicamento",
    "es_vehiculo",
    "es_vehiculo_usado",
    "es_vehiculo_nuevo",
    "es_pequeno_contribuyente",
    "es_no_afecta",
    "no_genera_credito_fiscal",
    "tiene_constancia_exencion",
    "es_exento",
]


async def _get_tenant_schemas() -> list[str]:
    """
    Retorna la lista de schemas de tenant (excluye schemas del sistema).
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('public', 'pg_catalog', 'information_schema')
              AND schema_name NOT LIKE 'pg\\_%'
              AND schema_name NOT LIKE '\\_timescaledb\\_%'
            ORDER BY schema_name
        """))
        return [row[0] for row in result.all()]


async def _tabla_existe(db, schema: str) -> bool:
    """Verifica si facturas_electronicas existe en el schema dado."""
    result = await db.execute(text("""
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = :schema
              AND table_name = 'facturas_electronicas'
        )
    """), {"schema": schema})
    return result.scalar()


async def _procesar_tenant(
    schema: str,
    limit: int | None,
    dry_run: bool,
    solo_no_clasificadas: bool,
) -> dict:
    """
    Procesa facturas de un tenant específico.
    
    Returns:
        Dict con estadísticas: {clasificadas, errores, total}
    """
    stats = {"clasificadas": 0, "errores": 0, "total": 0, "omitidas": 0}
    
    async with AsyncSessionLocal() as db:
        try:
            # Configurar search_path para este tenant
            await db.execute(text(f"SET LOCAL search_path TO {schema}, public"))
            
            # Verificar que la tabla existe
            if not await _tabla_existe(db, schema):
                logger.info(f"  ⏭️  {schema}: tabla facturas_electronicas no existe")
                return stats
            
            # Contar total
            stmt_count = select(func.count(FacturaElectronica.id))
            total_facturas = (await db.execute(stmt_count)).scalar() or 0
            stats["total"] = total_facturas
            logger.info(f"  📊 {schema}: {total_facturas} facturas totales")
            
            # Construir query base
            stmt = (
                select(FacturaElectronica)
                .options(
                    selectinload(FacturaElectronica.detalles),
                    selectinload(FacturaElectronica.impuestos_especiales)
                    .selectinload(FacturaImpuestoEspecial.catalogo),
                )
                .order_by(FacturaElectronica.id)
            )
            
            # Filtro: solo facturas no clasificadas
            if solo_no_clasificadas:
                # Factura "no clasificada" = todos los booleanos en False
                condiciones = [
                    getattr(FacturaElectronica, campo).is_(False)
                    for campo in CAMPOS_BOOLEANOS_CLASIFICACION
                    if hasattr(FacturaElectronica, campo)
                ]
                if condiciones:
                    stmt = stmt.where(and_(*condiciones))
            
            if limit:
                stmt = stmt.limit(limit)
            
            result = await db.execute(stmt)
            facturas = result.scalars().all()
            
            logger.info(f"  📦 {schema}: {len(facturas)} facturas a procesar")
            
            for idx, factura in enumerate(facturas, 1):
                try:
                    clasificacion = await clasificar_factura(db, factura)
                    
                    # Filtrar campos derivados (no existen en el modelo)
                    clasificacion_aplicable = {
                        k: v for k, v in clasificacion.items()
                        if k not in CAMPOS_DERIVADOS and hasattr(factura, k)
                    }
                    
                    if dry_run:
                        derived = clasificacion.get("clasificacion_gasto_sat_derived", "?")
                        logger.info(
                            f"    [{idx}/{len(facturas)}] Factura {factura.id}: "
                            f"derived={derived}, campos={clasificacion_aplicable}"
                        )
                    else:
                        for campo, valor in clasificacion_aplicable.items():
                            setattr(factura, campo, valor)
                        
                        # Flush periódico para no saturar memoria
                        if idx % 100 == 0:
                            await db.flush()
                            logger.info(f"    ✅ {schema}: procesadas {idx}/{len(facturas)}")
                    
                    stats["clasificadas"] += 1
                    
                except Exception as e:
                    logger.error(f"    ❌ {schema}: error en factura {factura.id}: {e}")
                    stats["errores"] += 1
            
            if not dry_run:
                await db.commit()
                logger.info(f"  ✅ {schema}: commit exitoso ({stats['clasificadas']} clasificadas)")
            else:
                logger.info(f"  🔍 {schema}: dry-run ({stats['clasificadas']} analizadas)")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"  ❌ {schema}: error crítico: {e}", exc_info=True)
            raise
    
    return stats


async def backfill(
    tenant: str | None = None,
    limit: int | None = None,
    dry_run: bool = False,
    solo_no_clasificadas: bool = False,
) -> None:
    """
    Clasifica facturas existentes en todos los tenants (o uno específico).
    """
    logger.info("=" * 70)
    logger.info("INICIANDO BACKFILL DE CLASIFICACIÓN DE FACTURAS")
    logger.info("=" * 70)
    
    if dry_run:
        logger.info("🔍 MODO DRY-RUN: No se aplicarán cambios")
    if solo_no_clasificadas:
        logger.info("🎯 MODO SELECTIVO: Solo facturas no clasificadas")
    if tenant:
        logger.info(f"🎯 TENANT ESPECÍFICO: {tenant}")
    if limit:
        logger.info(f"🎯 LÍMITE: {limit} facturas por tenant")
    
    # Obtener schemas de tenant
    schemas = await _get_tenant_schemas()
    
    # Filtrar si se especificó un tenant
    if tenant:
        if tenant not in schemas:
            logger.error(f"❌ Tenant '{tenant}' no encontrado. Disponibles: {schemas}")
            return
        schemas = [tenant]
    
    logger.info(f"📋 Tenants a procesar: {len(schemas)}")
    
    # Estadísticas globales
    total_clasificadas = 0
    total_errores = 0
    total_facturas = 0
    tenants_procesados = 0
    
    for idx, schema in enumerate(schemas, 1):
        logger.info(f"\n[{idx}/{len(schemas)}] Procesando tenant: {schema}")
        logger.info("-" * 50)
        
        try:
            stats = await _procesar_tenant(schema, limit, dry_run, solo_no_clasificadas)
            total_clasificadas += stats["clasificadas"]
            total_errores += stats["errores"]
            total_facturas += stats["total"]
            tenants_procesados += 1
        except Exception as e:
            logger.error(f"❌ Error procesando tenant {schema}: {e}")
            # Continuar con el siguiente tenant
            continue
    
    # Resumen final
    logger.info("\n" + "=" * 70)
    logger.info("RESUMEN FINAL")
    logger.info("=" * 70)
    logger.info(f"📊 Tenants procesados: {tenants_procesados}/{len(schemas)}")
    logger.info(f"📊 Total facturas analizadas: {total_facturas}")
    logger.info(f"✅ Facturas clasificadas: {total_clasificadas}")
    logger.info(f"❌ Errores: {total_errores}")
    if dry_run:
        logger.info("🔍 (Modo dry-run: no se aplicaron cambios)")
    logger.info("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Backfill de clasificación de facturas (multi-tenant)"
    )
    parser.add_argument(
        "--tenant",
        type=str,
        default=None,
        help="Procesar solo un tenant específico (default: todos)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Máximo de facturas por tenant (default: todas)",
    )
    parser.add_argument(
        "--solo-no-clasificadas",
        action="store_true",
        help="Solo procesar facturas con todos los booleanos en False",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo mostrar qué se haría sin aplicar cambios",
    )
    
    args = parser.parse_args()
    
    asyncio.run(backfill(
        tenant=args.tenant,
        limit=args.limit,
        dry_run=args.dry_run,
        solo_no_clasificadas=args.solo_no_clasificadas,
    ))


if __name__ == "__main__":
    main()
