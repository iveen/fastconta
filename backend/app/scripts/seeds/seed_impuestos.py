"""
Script para poblar el catálogo base de impuestos.
Idempotente: seguro de ejecutar múltiples veces.
Ejecutar: python -m app.scripts.seeds.seed_impuestos
"""
import asyncio
import os
import sys

from sqlalchemy import select

# Ajustar ruta para importar modelos desde la raíz del backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import AsyncSessionLocal
from app.models.global_models import CatalogoImpuesto
from app.scripts.data.impuestos import IMPUESTOS


async def seed():
    """Carga el catálogo base de impuestos."""
    print("=" * 70)
    print(" INICIANDO CARGA DE CATÁLOGO BASE DE IMPUESTOS ")
    print("=" * 70)
    
    async with AsyncSessionLocal() as db:
        try:
            print(f"\n💰 Sembrando {len(IMPUESTOS)} impuestos...")
            
            creados = 0
            actualizados = 0
            
            for imp_data in IMPUESTOS:
                # Buscar si ya existe por codigo (campo unique)
                stmt = select(CatalogoImpuesto).where(
                    CatalogoImpuesto.codigo == imp_data["codigo"]
                )
                result = await db.execute(stmt)
                existente = result.scalar_one_or_none()
                
                if existente:
                    # Actualizar si ya existe
                    for key, value in imp_data.items():
                        setattr(existente, key, value)
                    actualizados += 1
                    print(f"  ✅ Actualizado: {imp_data['codigo']} - {imp_data['nombre']}")
                else:
                    # Crear nuevo
                    nuevo = CatalogoImpuesto(**imp_data)
                    db.add(nuevo)
                    creados += 1
                    print(f"  ➕ Creado: {imp_data['codigo']} - {imp_data['nombre']}")
            
            # Commit final
            await db.commit()
            
            print("\n" + "=" * 70)
            print("✅ CARGA DE CATÁLOGO BASE DE IMPUESTOS COMPLETADA EXITOSAMENTE")
            print("=" * 70)
            print(f"  📊 Total procesados: {len(IMPUESTOS)}")
            print(f"  ➕ Creados: {creados}")
            print(f"   Actualizados: {actualizados}")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error durante el seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed())