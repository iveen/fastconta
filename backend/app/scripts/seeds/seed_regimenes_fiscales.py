"""
Script para poblar el catálogo de Regímenes Fiscales.
Idempotente: seguro de ejecutar múltiples veces.
Ejecutar: python -m app.scripts.seeds.seed_regimenes_fiscales
"""
import asyncio
import os
import sys

from sqlalchemy import select

# Ajustar ruta para importar modelos desde la raíz del backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import AsyncSessionLocal
from app.models.global_models import RegimenFiscal
from app.scripts.data.regimenes_fiscales import REGIMENES_FISCALES


async def seed():
    """Carga el catálogo de regímenes fiscales."""
    print("=" * 70)
    print(" INICIANDO CARGA DE REGÍMENES FISCALES (SAT) ")
    print("=" * 70)
    
    async with AsyncSessionLocal() as db:
        try:
            print(f"\n🏛️  Sembrando {len(REGIMENES_FISCALES)} regímenes fiscales...")
            
            creados = 0
            actualizados = 0
            
            for regimen_data in REGIMENES_FISCALES:
                # Buscar si ya existe por codigo (campo unique)
                stmt = select(RegimenFiscal).where(
                    RegimenFiscal.codigo == regimen_data["codigo"]
                )
                result = await db.execute(stmt)
                existente = result.scalar_one_or_none()
                
                if existente:
                    # Actualizar si ya existe
                    for key, value in regimen_data.items():
                        setattr(existente, key, value)
                    actualizados += 1
                    print(f"  ✅ Actualizado: {regimen_data['codigo']} - {regimen_data['nombre']}")
                else:
                    # Crear nuevo (is_active=True por defecto en el modelo)
                    nuevo = RegimenFiscal(**regimen_data)
                    db.add(nuevo)
                    creados += 1
                    print(f"  ➕ Creado: {regimen_data['codigo']} - {regimen_data['nombre']}")
            
            # Commit final
            await db.commit()
            
            print("\n" + "=" * 70)
            print("✅ CARGA DE REGÍMENES FISCALES COMPLETADA EXITOSAMENTE")
            print("=" * 70)
            print(f"  📊 Total procesados: {len(REGIMENES_FISCALES)}")
            print(f"  ➕ Creados: {creados}")
            print(f"   Actualizados: {actualizados}")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error durante el seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed())