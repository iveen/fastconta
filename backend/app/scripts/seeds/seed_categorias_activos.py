"""
Script para poblar el catálogo de Categorías de Activos Fijos.
Idempotente: seguro de ejecutar múltiples veces.
Ejecutar: python -m app.scripts.seeds.seed_categorias_activos
"""
import asyncio
import os
import sys

from sqlalchemy import select

# Ajustar ruta para importar modelos desde la raíz del backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import AsyncSessionLocal
from app.models.global_models import CategoriaActivoFijo
from app.scripts.data.categorias_activos import CATEGORIAS_ACTIVOS_FIJOS


async def seed():
    """Carga el catálogo de categorías de activos fijos."""
    print("=" * 70)
    print(" INICIANDO CARGA DE CATEGORÍAS DE ACTIVOS FIJOS ")
    print("=" * 70)
    
    async with AsyncSessionLocal() as db:
        try:
            print(f"\n🏗️  Sembrando {len(CATEGORIAS_ACTIVOS_FIJOS)} categorías de activos fijos...")
            
            creadas = 0
            actualizadas = 0
            
            for cat_data in CATEGORIAS_ACTIVOS_FIJOS:
                # Buscar si ya existe por nombre (campo unique)
                stmt = select(CategoriaActivoFijo).where(
                    CategoriaActivoFijo.nombre == cat_data["nombre"]
                )
                result = await db.execute(stmt)
                existente = result.scalar_one_or_none()
                
                if existente:
                    # Actualizar si ya existe
                    for key, value in cat_data.items():
                        setattr(existente, key, value)
                    actualizadas += 1
                    print(f"  ✅ Actualizada: {cat_data['codigo_prefijo']} - {cat_data['nombre']}")
                else:
                    # Crear nueva
                    nueva = CategoriaActivoFijo(**cat_data)
                    db.add(nueva)
                    creadas += 1
                    print(f"  ➕ Creada: {cat_data['codigo_prefijo']} - {cat_data['nombre']}")
            
            # Commit final
            await db.commit()
            
            print("\n" + "=" * 70)
            print("✅ CARGA DE CATEGORÍAS DE ACTIVOS FIJOS COMPLETADA EXITOSAMENTE")
            print("=" * 70)
            print(f"  📊 Total procesadas: {len(CATEGORIAS_ACTIVOS_FIJOS)}")
            print(f"  ➕ Creadas: {creadas}")
            print(f"   Actualizadas: {actualizadas}")
            print(f"  💰 Tasa máxima más alta: {max(c['tasa_maxima_anual'] for c in CATEGORIAS_ACTIVOS_FIJOS)}%")
            print(f"  📅 Vida útil más larga: {max(c['vida_util_meses_default'] for c in CATEGORIAS_ACTIVOS_FIJOS)} meses")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error durante el seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed())