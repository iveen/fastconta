"""
Script para poblar el catálogo de Tipos de DTE oficiales de la SAT.
Idempotente: seguro de ejecutar múltiples veces.
Ejecutar: python -m app.scripts.seeds.seed_tipos_dte
"""
import asyncio
import os
import sys

from sqlalchemy import select

# Ajustar ruta para importar modelos desde la raíz del backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import AsyncSessionLocal
from app.models.global_models import TipoDTE
from app.scripts.data.tipos_dte import TIPOS_DTE


async def seed():
    """Carga el catálogo de tipos de DTE."""
    print("=" * 70)
    print(" INICIANDO CARGA DE TIPOS DE DTE (SAT) ")
    print("=" * 70)
    
    async with AsyncSessionLocal() as db:
        try:
            print(f"\n🧾 Sembrando {len(TIPOS_DTE)} tipos de DTE...")
            
            creados = 0
            actualizados = 0
            
            for tipo_data in TIPOS_DTE:
                # Buscar si ya existe por codigo (campo unique)
                stmt = select(TipoDTE).where(
                    TipoDTE.codigo == tipo_data["codigo"]
                )
                result = await db.execute(stmt)
                existente = result.scalar_one_or_none()
                
                if existente:
                    # Actualizar si ya existe
                    for key, value in tipo_data.items():
                        setattr(existente, key, value)
                    actualizados += 1
                    print(f"  ✅ Actualizado: {tipo_data['codigo']} - {tipo_data['descripcion']}")
                else:
                    # Crear nuevo
                    nuevo = TipoDTE(**tipo_data)
                    db.add(nuevo)
                    creados += 1
                    print(f"  ➕ Creado: {tipo_data['codigo']} - {tipo_data['descripcion']}")
            
            # Commit final
            await db.commit()
            
            print("\n" + "=" * 70)
            print("✅ CARGA DE TIPOS DE DTE COMPLETADA EXITOSAMENTE")
            print("=" * 70)
            print(f"  📊 Total procesados: {len(TIPOS_DTE)}")
            print(f"  ➕ Creados: {creados}")
            print(f"   Actualizados: {actualizados}")
            print(f"  📌 Facturas: {sum(1 for t in TIPOS_DTE if t['es_factura'])}")
            print(f"  📌 Documentos complementarios: {sum(1 for t in TIPOS_DTE if t['requiere_complemento'])}")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error durante el seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed())