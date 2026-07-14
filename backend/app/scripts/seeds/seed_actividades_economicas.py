"""
Script para poblar el catálogo de Actividades Económicas de la SAT.
Idempotente: seguro de ejecutar múltiples veces.
Ejecutar: python -m app.scripts.seeds.seed_actividades_economicas
"""
import asyncio
import os
import sys

from sqlalchemy import select

# Ajustar ruta para importar modelos desde la raíz del backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import AsyncSessionLocal
from app.models.global_models import ActividadEconomicaSAT
from app.scripts.data.actividades_economicas import ACTIVIDADES_ECONOMICAS_SAT


async def seed():
    """Carga el catálogo de actividades económicas de la SAT."""
    print("=" * 70)
    print(" INICIANDO CARGA DE ACTIVIDADES ECONÓMICAS (SAT) ")
    print("=" * 70)
    
    async with AsyncSessionLocal() as db:
        try:
            print(f"\n💼 Sembrando {len(ACTIVIDADES_ECONOMICAS_SAT)} actividades económicas...")
            
            creadas = 0
            actualizadas = 0
            errores = 0
            
            for actividad_data in ACTIVIDADES_ECONOMICAS_SAT:
                try:
                    # Buscar si ya existe por codigo_sat (campo único)
                    stmt = select(ActividadEconomicaSAT).where(
                        ActividadEconomicaSAT.codigo_sat == actividad_data["codigo_sat"]
                    )
                    result = await db.execute(stmt)
                    existente = result.scalar_one_or_none()
                    
                    if existente:
                        # Actualizar si ya existe
                        for key, value in actividad_data.items():
                            setattr(existente, key, value)
                        actualizadas += 1
                    else:
                        # Crear nueva
                        nueva = ActividadEconomicaSAT(**actividad_data)
                        db.add(nueva)
                        creadas += 1
                
                except Exception as e:
                    errores += 1
                    print(f"  ❌ Error con {actividad_data.get('codigo_sat', 'UNKNOWN')}: {str(e)}")
                    continue
            
            # Commit final
            await db.commit()
            
            print("\n" + "=" * 70)
            print("✅ CARGA DE ACTIVIDADES ECONÓMICAS COMPLETADA EXITOSAMENTE")
            print("=" * 70)
            print(f"  📊 Total procesadas: {len(ACTIVIDADES_ECONOMICAS_SAT)}")
            print(f"  ➕ Creadas: {creadas}")
            print(f"   Actualizadas: {actualizadas}")
            if errores > 0:
                print(f"  ⚠️  Errores: {errores}")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error durante el seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed())