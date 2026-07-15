"""
Script para poblar el catálogo de Impuestos Especiales.
Idempotente: seguro de ejecutar múltiples veces.
Ejecutar: python -m app.scripts.seeds.seed_impuestos_especiales
"""
import asyncio
import os
import sys

from sqlalchemy import select

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import AsyncSessionLocal
from app.models.global_models import CatalogoImpuestoEspecial
from app.scripts.data.impuestos_especiales import IMPUESTOS_ESPECIALES


async def seed():
    print("=" * 70)
    print(" INICIANDO CARGA DE IMPUESTOS ESPECIALES ")
    print("=" * 70)
    
    async with AsyncSessionLocal() as db:
        try:
            print(f"\n🏭 Sembrando {len(IMPUESTOS_ESPECIALES)} impuestos especiales...")
            creados = 0
            actualizados = 0
            
            for imp_data in IMPUESTOS_ESPECIALES:
                stmt = select(CatalogoImpuestoEspecial).where(
                    CatalogoImpuestoEspecial.codigo == imp_data["codigo"]
                )
                result = await db.execute(stmt)
                existente = result.scalar_one_or_none()
                
                if existente:
                    for key, value in imp_data.items():
                        setattr(existente, key, value)
                    actualizados += 1
                    print(f"  ✅ Actualizado: {imp_data['codigo']}")
                else:
                    nuevo = CatalogoImpuestoEspecial(**imp_data)
                    db.add(nuevo)
                    creados += 1
                    print(f"  ➕ Creado: {imp_data['codigo']}")
            
            await db.commit()
            print("\n" + "=" * 70)
            print("✅ CARGA DE IMPUESTOS ESPECIALES COMPLETADA")
            print(f"  📊 Creados: {creados} | Actualizados: {actualizados}")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error durante el seed: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(seed())