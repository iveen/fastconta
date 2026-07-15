"""
Script para poblar el catálogo de Estados de Libro.
Idempotente: seguro de ejecutar múltiples veces.
Ejecutar: python -m app.scripts.seeds.seed_estados_libro

Nota: La data probablemente ya existe (cargada en migración),
pero este seed garantiza consistencia con el resto de catálogos.
"""
import asyncio
import os
import sys

from sqlalchemy import select

# Ajustar ruta para importar modelos desde la raíz del backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import AsyncSessionLocal
from app.models.global_models import EstadoLibro
from app.scripts.data.estados_libro import ESTADOS_LIBRO


async def seed():
    """Carga el catálogo de estados de libro."""
    print("=" * 70)
    print(" INICIANDO CARGA DE ESTADOS DE LIBRO ")
    print("=" * 70)
    
    async with AsyncSessionLocal() as db:
        try:
            print(f"\n📋 Sembrando {len(ESTADOS_LIBRO)} estados de libro...")
            
            creados = 0
            actualizados = 0
            
            for estado_data in ESTADOS_LIBRO:
                # Buscar si ya existe por nombre
                stmt = select(EstadoLibro).where(
                    EstadoLibro.nombre == estado_data["nombre"]
                )
                result = await db.execute(stmt)
                existente = result.scalars().first()  # first() en lugar de scalar_one_or_none() porque no hay unique
                
                if existente:
                    # Actualizar si ya existe
                    for key, value in estado_data.items():
                        setattr(existente, key, value)
                    actualizados += 1
                    print(f"  ✅ Actualizado: {estado_data['nombre']}")
                else:
                    # Crear nuevo
                    nuevo = EstadoLibro(**estado_data)
                    db.add(nuevo)
                    creados += 1
                    print(f"  ➕ Creado: {estado_data['nombre']}")
            
            # Commit final
            await db.commit()
            
            print("\n" + "=" * 70)
            print("✅ CARGA DE ESTADOS DE LIBRO COMPLETADA EXITOSAMENTE")
            print("=" * 70)
            print(f"  📊 Total procesados: {len(ESTADOS_LIBRO)}")
            print(f"  ➕ Creados: {creados}")
            print(f"   Actualizados: {actualizados}")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error durante el seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed())