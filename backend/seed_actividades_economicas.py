#!/usr/bin/env python3
"""
Script para poblar actividades económicas SAT desde reporte TR2026.
Maneja duplicados por período mensual y extrae valores únicos.

Uso:
    python seed_actividades_sat_tr2026.py ruta/a/TR2026.xlsx
"""
import asyncio
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from app.config import settings


async def seed_actividades_sat(archivo_excel: str):
    if not Path(archivo_excel).exists():
        print(f"❌ Error: No se encontró {archivo_excel}")
        sys.exit(1)

    print(f"📖 Leyendo reporte SAT: {Path(archivo_excel).name}")
    
    # Leer la hoja (ajustar sheet_name si es necesario)
    df = pd.read_excel(archivo_excel, sheet_name=0)
    
    # Mapeo de columnas del Excel a nuestro modelo
    # Ajusta los nombres exactos según tu archivo
    columnas_map = {
        "Código Actividad": "codigo_sat",
        "Nombre Actividad": "nombre_actividad", 
        "Nombre Sección": "seccion"
    }
    
    # Verificar que existan las columnas esperadas
    cols_existentes = [c for c in columnas_map.keys() if c in df.columns]
    if len(cols_existentes) < 3:
        print(f"❌ Error: Columnas esperadas no encontradas. Encontradas: {list(df.columns)}")
        sys.exit(1)
    
    # Renombrar y seleccionar columnas relevantes
    df_clean = df[list(columnas_map.keys())].rename(columns=columnas_map)
    
    # Limpiar datos: eliminar NaN, espacios, duplicados exactos
    df_clean = df_clean.dropna(subset=["codigo_sat", "nombre_actividad"])
    df_clean["codigo_sat"] = df_clean["codigo_sat"].astype(str).str.strip()
    df_clean["nombre_actividad"] = df_clean["nombre_actividad"].astype(str).str.strip()
    df_clean["seccion"] = df_clean["seccion"].astype(str).str.replace("nan", "", regex=False).str.strip()
    
    # Eliminar duplicados por código + nombre (mantener primero)
    df_unique = df_clean.drop_duplicates(subset=["codigo_sat", "nombre_actividad"], keep="first")
    
    # Eliminar filas con código vacío o inválido
    df_unique = df_unique[df_unique["codigo_sat"].str.len() > 0]
    
    print(f"   ✓ {len(df)} filas leídas del reporte")
    print(f"   ✓ {len(df_unique)} actividades únicas después de deduplicar")

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        insertados = 0
        actualizados = 0
        saltados = 0

        for _, row in df_unique.iterrows():
            codigo = row["codigo_sat"]
            nombre_actividad = row["nombre_actividad"]
            seccion = row["seccion"] if row["seccion"] else None

            # 1. Verificar si ya existe por código SAT
            res = await session.execute(
                text("SELECT id FROM public.actividades_economicas_sat WHERE codigo_sat = :codigo"),
                {"codigo": codigo}
            )
            existing_id = res.scalar_one_or_none()

            if existing_id:
                # Actualizar solo si el nombre o sección cambiaron
                await session.execute(
                    text("""
                        UPDATE public.actividades_economicas_sat
                        SET nombre_actividad = :nombre_actividad, seccion = :seccion, activa = true
                        WHERE id = :id AND (nombre_actividad != :nombre OR seccion IS DISTINCT FROM :seccion)
                    """),
                    {"id": existing_id, "nombre_actividad": nombre_actividad, "seccion": seccion}
                )
                if res.rowcount > 0:
                    actualizados += 1
                else:
                    saltados += 1
                continue

            # 2. Insertar nuevo registro
            await session.execute(
                text("""
                    INSERT INTO public.actividades_economicas_sat 
                    (id, codigo_sat, nombre_actividad, seccion, activa)
                    VALUES (gen_random_uuid(), :codigo, :nombre_actividad, :seccion, true)
                """),
                {"codigo": codigo, "nombre_actividad": nombre_actividad, "seccion": seccion}
            )
            insertados += 1

            if insertados % 100 == 0:
                await session.commit()
                print(f"   → {insertados} actividades procesadas...")

        await session.commit()
        
        print(f"\n📊 Resumen:")
        print(f"   ✅ {insertados} actividades insertadas")
        print(f"   🔄 {actualizados} actividades actualizadas")
        print(f"   ⏭️  {saltados} actividades sin cambios")
        print("✅ Catálogo de actividades SAT cargado exitosamente.")

    await engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python seed_actividades_sat_tr2026.py <ruta_archivo.xlsx>")
        sys.exit(1)
    asyncio.run(seed_actividades_sat(sys.argv[1]))