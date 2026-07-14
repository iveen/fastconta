"""
Script para poblar las tablas de Departamentos y Municipios de Guatemala.
Fuente: Instituto Nacional de Estadística (INE)
Ejecutar: python -m app.scripts.seeds.seed_geografia
"""
import asyncio
import os
import sys

from sqlalchemy import select

# Ajustar ruta para importar modelos desde la raíz del backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import AsyncSessionLocal
from app.models.global_models import Departamento, Municipio
from app.scripts.data.geografia import DEPARTAMENTOS, MUNICIPIOS


async def seed_departamentos(db) -> dict:
    """
    Inserta o actualiza los departamentos.
    Retorna un diccionario {codigo_iso: id} para usar en municipios.
    """
    print("\n📍 Sembrando Departamentos...")
    dept_map = {}
    
    for dept_data in DEPARTAMENTOS:
        # Buscar si ya existe
        stmt = select(Departamento).where(Departamento.codigo_iso == dept_data["codigo_iso"])
        result = await db.execute(stmt)
        existente = result.scalar_one_or_none()
        
        if existente:
            # Actualizar
            existente.nombre = dept_data["nombre"]
            dept_map[dept_data["codigo_iso"]] = existente.id
            print(f"  ✅ Actualizado: {dept_data['codigo_iso']} - {dept_data['nombre']}")
        else:
            # Crear nuevo
            nuevo = Departamento(**dept_data)
            db.add(nuevo)
            await db.flush()  # Para obtener el ID generado
            dept_map[dept_data["codigo_iso"]] = nuevo.id
            print(f"  ➕ Creado: {dept_data['codigo_iso']} - {dept_data['nombre']}")
    
    return dept_map


async def seed_municipios(db, dept_map: dict):
    """
    Inserta o actualiza los municipios usando el mapa de departamentos.
    """
    print("\n🏘️  Sembrando Municipios...")
    
    for mun_data in MUNICIPIOS:
        # Obtener el departamento_id del mapa
        dept_codigo = mun_data.pop("departamento_codigo")
        departamento_id = dept_map.get(dept_codigo)
        
        if not departamento_id:
            print(f"  ⚠️  Error: No se encontró departamento con código {dept_codigo} para municipio {mun_data['nombre']}")
            continue
        
        # Buscar si ya existe
        stmt = select(Municipio).where(Municipio.codigo_iso == mun_data["codigo_iso"])
        result = await db.execute(stmt)
        existente = result.scalar_one_or_none()
        
        if existente:
            # Actualizar
            existente.nombre = mun_data["nombre"]
            existente.departamento_id = departamento_id
            print(f"  ✅ Actualizado: {mun_data['codigo_iso']} - {mun_data['nombre']}")
        else:
            # Crear nuevo
            nuevo = Municipio(
                codigo_iso=mun_data["codigo_iso"],
                nombre=mun_data["nombre"],
                departamento_id=departamento_id
            )
            db.add(nuevo)
            print(f"  ➕ Creado: {mun_data['codigo_iso']} - {mun_data['nombre']}")


async def seed():
    """Función principal del seed."""
    print("=" * 70)
    print(" INICIANDO CARGA DE GEOGRAFÍA (GUATEMALA) ")
    print("=" * 70)
    
    async with AsyncSessionLocal() as db:
        try:
            # Primero departamentos
            dept_map = await seed_departamentos(db)
            
            # Luego municipios
            await seed_municipios(db, dept_map)
            
            # Commit final
            await db.commit()
            
            print("\n" + "=" * 70)
            print("✅ CARGA DE GEOGRAFÍA COMPLETADA EXITOSAMENTE")
            print("=" * 70)
            print(f"  📊 Departamentos: {len(DEPARTAMENTOS)}")
            print(f"  📊 Municipios: {len(MUNICIPIOS)}")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error durante el seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed())