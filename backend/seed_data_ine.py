#!/usr/bin/env python3
"""
Script para poblar departamentos y municipios de Guatemala desde Excel.
Usa la misma lógica async y conexión directa que seed_plan_cuentas.py.

Uso:
    python seed_data_ine.py
"""
import asyncio
import sys
import uuid
from pathlib import Path
import pandas as pd

# Ajustar el path para poder importar la configuración de la app
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from app.config import settings


async def seed_geografia():
    """Función principal para poblar geografía de Guatemala."""
    
    excel_path = Path(__file__).parent.parent / "INE_Geografia_Guatemala.xlsx"
    if not excel_path.exists():
        print(f"❌ Error: No se encontró el archivo {excel_path}")
        sys.exit(1)

    print(f"📖 Leyendo Excel: {excel_path.name}")
    
    # Leer las dos hojas del Excel
    df_deptos = pd.read_excel(excel_path, sheet_name='Departamentos')
    df_munis = pd.read_excel(excel_path, sheet_name='Municipios')

    # Limpiar strings (eliminar espacios en blanco)
    for df in [df_deptos, df_munis]:
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].str.strip()

    print(f"   ✓ {len(df_deptos)} departamentos cargados del Excel")
    print(f"   ✓ {len(df_munis)} municipios cargados del Excel")

    # Crear engine y sesión async
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Mapeo: código_iso departamento -> uuid
        depto_map = {}
        
        # ==========================================
        # 1️⃣ INSERTAR DEPARTAMENTOS
        # ==========================================
        print("\n🏛️  Poblando tabla DEPARTAMENTOS...")
        
        insertados_deptos = 0
        saltados_deptos = 0
        
        for _, row in df_deptos.iterrows():
            codigo = str(row['Código']).zfill(2)  # Asegurar 2 dígitos: "01", "02", etc.
            nombre = row['Nombre']

            # Verificar si ya existe por codigo_iso
            res = await session.execute(
                text("""
                    SELECT id FROM public.departamentos 
                    WHERE codigo_iso = :codigo
                """),
                {"codigo": codigo}
            )
            existing = res.scalar_one_or_none()
            
            if existing:
                depto_map[codigo] = existing
                saltados_deptos += 1
                continue

            # Insertar nuevo departamento
            result = await session.execute(
                text("""
                    INSERT INTO public.departamentos (id, codigo_iso, nombre)
                    VALUES (gen_random_uuid(), :codigo, :nombre)
                    RETURNING id
                """),
                {"codigo": codigo, "nombre": nombre}
            )
            depto_id = result.scalar_one()
            depto_map[codigo] = depto_id
            insertados_deptos += 1
            
            if insertados_deptos % 5 == 0:
                print(f"   → {insertados_deptos} departamentos procesados...")

        await session.commit()
        print(f"   ✅ {insertados_deptos} departamentos insertados")
        if saltados_deptos > 0:
            print(f"   ⏭️  {saltados_deptos} departamentos ya existían")

        # ==========================================
        # 2️⃣ INSERTAR MUNICIPIOS
        # ==========================================
        print("\n🏘️  Poblando tabla MUNICIPIOS...")
        
        insertados_munis = 0
        saltados_munis = 0
        errores = 0
        
        for _, row in df_munis.iterrows():
            codigo_mun = str(row['Código']).zfill(4)  # "0101", "0102", etc.
            nombre_mun = row['Nombre']
            codigo_depto = str(row['Departamento']).zfill(2)  # "01", "02", etc.

            # Buscar el UUID del departamento
            depto_id = depto_map.get(codigo_depto)
            if not depto_id:
                print(f"   ❌ Departamento {codigo_depto} no encontrado para municipio {nombre_mun}")
                errores += 1
                continue

            # Verificar si ya existe por codigo_iso + nombre
            res = await session.execute(
                text("""
                    SELECT id FROM public.municipios 
                    WHERE codigo_iso = :codigo AND nombre = :nombre
                """),
                {"codigo": codigo_mun, "nombre": nombre_mun}
            )
            if res.scalar_one_or_none():
                saltados_munis += 1
                continue

            # Insertar nuevo municipio
            try:
                await session.execute(
                    text("""
                        INSERT INTO public.municipios (id, codigo_iso, nombre, departamento_id)
                        VALUES (gen_random_uuid(), :codigo, :nombre, :depto_id)
                    """),
                    {"codigo": codigo_mun, "nombre": nombre_mun, "depto_id": depto_id}
                )
                insertados_munis += 1

                # Commit por lotes cada 50 municipios
                if insertados_munis % 50 == 0:
                    await session.commit()
                    print(f"   → {insertados_munis} municipios procesados...")
                    
            except Exception as e:
                print(f"   ⚠️  Error al insertar municipio {nombre_mun}: {e}")
                errores += 1
                continue

        await session.commit()
        print(f"   ✅ {insertados_munis} municipios insertados")
        if saltados_munis > 0:
            print(f"   ⏭️  {saltados_munis} municipios ya existían")
        if errores > 0:
            print(f"   ❌ {errores} errores encontrados")

        # ==========================================
        # 3️⃣ VALIDACIÓN FINAL
        # ==========================================
        print("\n📊 Validación final...")
        
        total_deptos = await session.scalar(text("SELECT count(*) FROM public.departamentos"))
        total_munis = await session.scalar(text("SELECT count(*) FROM public.municipios"))
        
        # Verificar municipios sin departamento
        munis_sin_depto = await session.scalar(text("""
            SELECT count(*) FROM public.municipios m
            LEFT JOIN public.departamentos d ON m.departamento_id = d.id
            WHERE d.id IS NULL
        """))
        
        # Contar municipios por departamento
        print("\n📋 Distribución por departamento:")
        result = await session.execute(text("""
            SELECT d.codigo_iso, d.nombre, count(m.id) as total_municipios
            FROM public.departamentos d
            LEFT JOIN public.municipios m ON d.id = m.departamento_id
            GROUP BY d.id, d.codigo_iso, d.nombre
            ORDER BY d.codigo_iso
        """))
        
        for codigo, nombre, total in result.fetchall():
            print(f"   {codigo} - {nombre:30s}: {total} municipios")

        print(f"\n✅ Total departamentos: {total_deptos}")
        print(f"✅ Total municipios: {total_munis}")
        
        if munis_sin_depto > 0:
            print(f"❌ ALERTA: {munis_sin_depto} municipios sin departamento válido")
        else:
            print("✅ Todos los municipios tienen departamento asignado correctamente")

    await engine.dispose()
    
    print("\n" + "=" * 60)
    print("✅ SEED GEOGRAFÍA DE GUATEMALA COMPLETADO EXITOSAMENTE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed_geografia())