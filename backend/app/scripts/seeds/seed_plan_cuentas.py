"""
Script para poblar el Plan de Cuentas base de una empresa.
Idempotente: seguro de ejecutar múltiples veces.

Uso:
    # Cargar para la primera empresa encontrada
    python -m app.scripts.seeds.seed_plan_cuentas
    
    # Cargar para una empresa específica (por ID)
    python -m app.scripts.seeds.seed_plan_cuentas --empresa-id 1
"""
import argparse
import asyncio
import os
import sys

from sqlalchemy import select

# Ajustar ruta para importar modelos desde la raíz del backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from app.db.session import AsyncSessionLocal
from app.models.tenant_models import CuentaContable, Empresa
from app.scripts.data.plan_cuentas import PLAN_CUENTAS_BASE


async def seed(empresa_id: int | None = None):
    """Carga el plan de cuentas base para una empresa."""
    print("=" * 70)
    print("📊 INICIANDO CARGA DE PLAN DE CUENTAS BASE")
    print("=" * 70)
    
    async with AsyncSessionLocal() as db:
        try:
            # Determinar empresa objetivo
            if empresa_id:
                stmt = select(Empresa).where(Empresa.id == empresa_id)
                result = await db.execute(stmt)
                empresa = result.scalar_one_or_none()
                if not empresa:
                    print(f"❌ Error: No se encontró la empresa con ID {empresa_id}")
                    return
            else:
                # Buscar la primera empresa activa
                stmt = select(Empresa).where(Empresa.is_active.is_(True)).limit(1)
                result = await db.execute(stmt)
                empresa = result.scalar_one_or_none()
                if not empresa:
                    print("❌ Error: No se encontró ninguna empresa activa en el sistema")
                    return
            
            print(f"\n Empresa objetivo: {empresa.nombre} (ID: {empresa.id})")
            print(f" Sembrando {len(PLAN_CUENTAS_BASE)} cuentas contables...\n")
            
            creadas = 0
            actualizadas = 0
            omitidas = 0
            
            # Mapeo de código a ID para resolver cuentas padre
            codigo_a_id = {}
            
            # Primero, cargar cuentas existentes para esta empresa
            stmt = select(CuentaContable).where(
                CuentaContable.empresa_id == empresa.id,
                CuentaContable.is_active.is_(True)
            )
            result = await db.execute(stmt)
            cuentas_existentes = result.scalars().all()
            
            for cuenta in cuentas_existentes:
                codigo_a_id[cuenta.codigo] = cuenta.id
            
            # Procesar cada cuenta del seed
            for cuenta_data in PLAN_CUENTAS_BASE:
                codigo = cuenta_data["codigo"]
                
                # Verificar si ya existe
                if codigo in codigo_a_id:
                    # Actualizar si ya existe
                    stmt = select(CuentaContable).where(
                        CuentaContable.id == codigo_a_id[codigo]
                    )
                    result = await db.execute(stmt)
                    existente = result.scalar_one_or_none()
                    
                    if existente:
                        for key, value in cuenta_data.items():
                            if key != "padre":  # No actualizar el campo padre directamente
                                setattr(existente, key, value)
                        actualizadas += 1
                        print(f"  ✅ Actualizada: {codigo} - {cuenta_data['nombre']}")
                else:
                    # Resolver cuenta padre si existe
                    cuenta_padre_id = None
                    if "padre" in cuenta_data and cuenta_data["padre"]:
                        padre_codigo = cuenta_data["padre"]
                        if padre_codigo in codigo_a_id:
                            cuenta_padre_id = codigo_a_id[padre_codigo]
                        else:
                            print(f"  ⚠️  Advertencia: Cuenta padre '{padre_codigo}' no encontrada para {codigo}")
                    
                    # Crear nueva cuenta
                    nueva_cuenta = CuentaContable(
                        codigo=codigo,
                        nombre=cuenta_data["nombre"],
                        tipo=cuenta_data["tipo"],
                        naturaleza=cuenta_data["naturaleza"],
                        nivel=cuenta_data["nivel"],
                        acepta_tercero=cuenta_data.get("acepta_tercero", False),
                        cuenta_padre_id=cuenta_padre_id,
                        empresa_id=empresa.id,
                        is_active=True
                    )
                    db.add(nueva_cuenta)
                    await db.flush()  # Obtener el ID generado
                    
                    codigo_a_id[codigo] = nueva_cuenta.id
                    creadas += 1
                    print(f"  ➕ Creada: {codigo} - {cuenta_data['nombre']}")
            
            # Commit final
            await db.commit()
            
            print("\n" + "=" * 70)
            print("✅ CARGA DE PLAN DE CUENTAS COMPLETADA EXITOSAMENTE")
            print("=" * 70)
            print(f"  📊 Total procesadas: {len(PLAN_CUENTAS_BASE)}")
            print(f"  ➕ Creadas: {creadas}")
            print(f"  🔄 Actualizadas: {actualizadas}")
            print(f"  ⏭️  Omitidas: {omitidas}")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error durante el seed: {e}")
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cargar plan de cuentas base para una empresa")
    parser.add_argument(
        "--empresa-id",
        type=int,
        help="ID de la empresa (BIGINT). Si no se especifica, usa la primera empresa activa."
    )
    args = parser.parse_args()
    
    asyncio.run(seed(args.empresa_id))