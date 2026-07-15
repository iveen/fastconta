"""
Script para poblar la tabla puente de Configuración Régimen-Impuesto.
Idempotente: seguro de ejecutar múltiples veces.
Ejecutar: python -m app.scripts.seeds.seed_regimen_impuesto_config
"""
import asyncio
import os
import sys

from sqlalchemy import select

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import AsyncSessionLocal
from app.models.global_models import (
    CatalogoImpuesto,
    RegimenFiscal,
    RegimenImpuestoConfig,
)
from app.scripts.data.regimen_impuesto_config import REGIMEN_IMPUESTO_CONFIG


async def seed():
    print("=" * 70)
    print(" INICIANDO CARGA DE CONFIGURACIÓN RÉGIMEN-IMPUESTO ")
    print("=" * 70)
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. Construir mapas de IDs para resolución de FKs
            stmt_regimenes = select(RegimenFiscal.codigo, RegimenFiscal.id)
            regimenes_map = {row.codigo: row.id for row in (await db.execute(stmt_regimenes)).all()}
            
            stmt_impuestos = select(CatalogoImpuesto.codigo, CatalogoImpuesto.id)
            impuestos_map = {row.codigo: row.id for row in (await db.execute(stmt_impuestos)).all()}
            
            print(f"\n🔗 Resolviendo {len(REGIMEN_IMPUESTO_CONFIG)} configuraciones...")
            creadas = 0
            actualizadas = 0
            omitidas = 0
            
            for config_data in REGIMEN_IMPUESTO_CONFIG:
                regimen_cod = config_data.pop("regimen_codigo")
                impuesto_cod = config_data.pop("impuesto_codigo")
                
                regimen_id = regimenes_map.get(regimen_cod)
                impuesto_id = impuestos_map.get(impuesto_cod)
                
                if not regimen_id or not impuesto_id:
                    print(f"  ⚠️  Omitido: Falta régimen '{regimen_cod}' o impuesto '{impuesto_cod}' en la BD")
                    omitidas += 1
                    continue
                
                config_data["regimen_id"] = regimen_id
                config_data["impuesto_id"] = impuesto_id
                
                # 2. Buscar si la configuración ya existe (UniqueConstraint: regimen_id + impuesto_id)
                stmt = select(RegimenImpuestoConfig).where(
                    RegimenImpuestoConfig.regimen_id == regimen_id,
                    RegimenImpuestoConfig.impuesto_id == impuesto_id
                )
                result = await db.execute(stmt)
                existente = result.scalar_one_or_none()
                
                if existente:
                    for key, value in config_data.items():
                        setattr(existente, key, value)
                    actualizadas += 1
                    print(f"  ✅ Actualizado: {regimen_cod} + {impuesto_cod}")
                else:
                    nuevo = RegimenImpuestoConfig(**config_data)
                    db.add(nuevo)
                    creadas += 1
                    print(f"  ➕ Creado: {regimen_cod} + {impuesto_cod}")
            
            await db.commit()
            
            print("\n" + "=" * 70)
            print("✅ CARGA DE CONFIGURACIÓN RÉGIMEN-IMPUESTO COMPLETADA")
            print(f"  📊 Creadas: {creadas} | Actualizadas: {actualizadas} | Omitidas: {omitidas}")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error durante el seed: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(seed())