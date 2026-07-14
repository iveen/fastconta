"""
Script para poblar el catálogo de Tipos de Libro.
Idempotente: seguro de ejecutar múltiples veces.
Ejecutar: python -m app.scripts.seeds.seed_tipos_libro
"""
import asyncio
import os
import sys

from sqlalchemy import select

# Ajustar ruta para importar modelos desde la raíz del backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import AsyncSessionLocal
from app.models.global_models import TipoLibro
from app.scripts.data.tipos_libro import TIPOS_LIBRO


async def seed():
    """Carga el catálogo de tipos de libro."""
    print("=" * 70)
    print(" INICIANDO CARGA DE TIPOS DE LIBRO ")
    print("=" * 70)
    
    async with AsyncSessionLocal() as db:
        try:
            print(f"\n📚 Sembrando {len(TIPOS_LIBRO)} tipos de libro...")
            
            creados = 0
            actualizados = 0
            
            for tipo_data in TIPOS_LIBRO:
                # Buscar si ya existe por nombre (campo unique)
                stmt = select(TipoLibro).where(
                    TipoLibro.nombre == tipo_data["nombre"]
                )
                result = await db.execute(stmt)
                existente = result.scalar_one_or_none()
                
                if existente:
                    # Actualizar si ya existe
                    for key, value in tipo_data.items():
                        setattr(existente, key, value)
                    actualizados += 1
                    print(f"  ✅ Actualizado: {tipo_data['codigo']} - {tipo_data['nombre']}")
                else:
                    # Crear nuevo
                    nuevo = TipoLibro(**tipo_data)
                    db.add(nuevo)
                    creados += 1
                    print(f"  ➕ Creado: {tipo_data['codigo']} - {tipo_data['nombre']}")
            
            # Commit final
            await db.commit()
            
            print("\n" + "=" * 70)
            print("✅ CARGA DE TIPOS DE LIBRO COMPLETADA EXITOSAMENTE")
            print("=" * 70)
            print(f"  📊 Total procesados: {len(TIPOS_LIBRO)}")
            print(f"  ➕ Creados: {creados}")
            print(f"   Actualizados: {actualizados}")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error durante el seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed())