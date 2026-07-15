"""
Script para poblar el catálogo de Roles de Acceso (RBAC).
Idempotente: seguro de ejecutar múltiples veces.
Ejecutar: python -m app.scripts.seeds.seed_roles

Nota: La data probablemente ya existe (cargada en migración inicial),
pero este seed garantiza consistencia con el resto de catálogos globales.
"""
import asyncio
import os
import sys

from sqlalchemy import select

# Ajustar ruta para importar modelos desde la raíz del backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import AsyncSessionLocal
from app.models.global_models import Role
from app.scripts.data.roles import ROLES


async def seed():
    """Carga el catálogo de roles de acceso."""
    print("=" * 70)
    print(" INICIANDO CARGA DE ROLES DE ACCESO (RBAC) ")
    print("=" * 70)
    
    async with AsyncSessionLocal() as db:
        try:
            print(f"\n🛡️  Sembrando {len(ROLES)} roles de acceso...")
            
            creados = 0
            actualizados = 0
            
            for role_data in ROLES:
                # Buscar si ya existe por codigo (campo unique en el modelo)
                stmt = select(Role).where(
                    Role.codigo == role_data["codigo"]
                )
                result = await db.execute(stmt)
                existente = result.scalar_one_or_none()
                
                if existente:
                    # Actualizar si ya existe
                    for key, value in role_data.items():
                        setattr(existente, key, value)
                    actualizados += 1
                    print(f"  ✅ Actualizado: {role_data['codigo']} - {role_data['nombre']}")
                else:
                    # Crear nuevo
                    nuevo = Role(**role_data)
                    db.add(nuevo)
                    creados += 1
                    print(f"  ➕ Creado: {role_data['codigo']} - {role_data['nombre']}")
            
            # Commit final
            await db.commit()
            
            print("\n" + "=" * 70)
            print("✅ CARGA DE ROLES DE ACCESO COMPLETADA EXITOSAMENTE")
            print("=" * 70)
            print(f"  📊 Total procesados: {len(ROLES)}")
            print(f"  ➕ Creados: {creados}")
            print(f"   Actualizados: {actualizados}")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error durante el seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed())