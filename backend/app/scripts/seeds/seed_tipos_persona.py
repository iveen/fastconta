"""
Script para poblar el catálogo de Tipos de Persona.
Idempotente: seguro de ejecutar múltiples veces.
Ejecutar: python -m app.scripts.seeds.seed_tipos_persona
"""
import asyncio
import os
import sys

from sqlalchemy import select

# Ajustar ruta para importar modelos desde la raíz del backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import AsyncSessionLocal
from app.models.global_models import TipoPersona
from app.scripts.data.tipos_persona import TIPOS_PERSONA


async def seed():
    """Carga el catálogo de tipos de persona."""
    print("=" * 70)
    print(" INICIANDO CARGA DE TIPOS DE PERSONA ")
    print("=" * 70)
    
    async with AsyncSessionLocal() as db:
        try:
            print(f"\n👤 Sembrando {len(TIPOS_PERSONA)} tipos de persona...")
            
            creadas = 0
            actualizadas = 0
            
            for tipo_data in TIPOS_PERSONA:
                # Buscar si ya existe por nombre (campo unique)
                stmt = select(TipoPersona).where(
                    TipoPersona.nombre == tipo_data["nombre"]
                )
                result = await db.execute(stmt)
                existente = result.scalar_one_or_none()
                
                if existente:
                    # Actualizar si ya existe
                    for key, value in tipo_data.items():
                        setattr(existente, key, value)
                    actualizadas += 1
                    print(f"  ✅ Actualizado: {tipo_data['nombre']}")
                else:
                    # Crear nuevo
                    nuevo = TipoPersona(**tipo_data)
                    db.add(nuevo)
                    creadas += 1
                    print(f"  ➕ Creado: {tipo_data['nombre']}")
            
            # Commit final
            await db.commit()
            
            print("\n" + "=" * 70)
            print("✅ CARGA DE TIPOS DE PERSONA COMPLETADA EXITOSAMENTE")
            print("=" * 70)
            print(f"  📊 Total procesados: {len(TIPOS_PERSONA)}")
            print(f"  ➕ Creados: {creadas}")
            print(f"   Actualizados: {actualizadas}")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error durante el seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed())