"""
Script para poblar el catálogo de monedas oficiales del BANGUAT.
Idempotente: seguro de ejecutar múltiples veces.
Ejecutar: python -m app.scripts.seeds.seed_monedas
"""
import asyncio
import os
import sys

from sqlalchemy import select

# Ajustar ruta para importar modelos desde la raíz del backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import AsyncSessionLocal
from app.models.global_models import CatalogoMoneda
from app.scripts.data.monedas import MONEDAS_BANGUAT


async def seed():
    """Carga el catálogo de monedas del BANGUAT."""
    print("=" * 70)
    print(" INICIANDO CARGA DE CATÁLOGO DE MONEDAS (BANGUAT) ")
    print("=" * 70)
    
    async with AsyncSessionLocal() as db:
        try:
            print(f"\n💱 Sembrando {len(MONEDAS_BANGUAT)} monedas...")
            
            creadas = 0
            actualizadas = 0
            errores = 0
            
            for moneda_data in MONEDAS_BANGUAT:
                try:
                    # Buscar si ya existe por codigo_iso (campo único)
                    stmt = select(CatalogoMoneda).where(
                        CatalogoMoneda.codigo_iso == moneda_data["codigo_iso"]
                    )
                    result = await db.execute(stmt)
                    existente = result.scalar_one_or_none()
                    
                    if existente:
                        # Actualizar si ya existe
                        for key, value in moneda_data.items():
                            setattr(existente, key, value)
                        actualizadas += 1
                        print(f"  ✅ Actualizada: {moneda_data['codigo_iso']} - {moneda_data['nombre']}")
                    else:
                        # Crear nueva
                        nueva = CatalogoMoneda(**moneda_data)
                        db.add(nueva)
                        creadas += 1
                        print(f"   Creada: {moneda_data['codigo_iso']} - {moneda_data['nombre']}")
                
                except Exception as e:
                    errores += 1
                    print(f"  ❌ Error con {moneda_data.get('codigo_iso', 'UNKNOWN')}: {str(e)}")
                    continue
            
            # Commit final
            await db.commit()
            
            print("\n" + "=" * 70)
            print("✅ CARGA DE MONEDAS COMPLETADA EXITOSAMENTE")
            print("=" * 70)
            print(f"  📊 Total procesadas: {len(MONEDAS_BANGUAT)}")
            print(f"  ➕ Creadas: {creadas}")
            print(f"   Actualizadas: {actualizadas}")
            if errores > 0:
                print(f"  ️  Errores: {errores}")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error durante el seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed())