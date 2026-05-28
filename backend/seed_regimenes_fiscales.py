#!/usr/bin/env python3
"""
Script para insertar los Regímenes Fiscales vigentes en Guatemala.
Uso:
    python scripts/seed_regimenes_fiscales.py
"""
import asyncio
import sys
from pathlib import Path

# Ajustar path para importar configuración de la app
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from app.config import settings

# Lista de regímenes fiscales según Decreto 10-2012
# NOTA: Pequeño Contribuyente se duplica para diferenciar tasas 4% vs 5%
REGIMENES_FISCALES = [
    "Pequeño Contribuyente Electrónico - 4%",         # Art. 45 - Electrónico (FEL)
    "Pequeño Contribuyente Manual - 5%",         # Art. 45 - Tradicional (papel)
    "Opcional Simplificado",         # Art. 46 - Ingresos hasta Q30,000/mes
    "Sobre Utilidades",                 # Art. 44 - 25% sobre utilidad neta
    "Rentas del Trabajo",               # Art. 65 - Personas Naturales (tabla progresiva)
    "Especial Agropecuario",            # Régimen específico campo
    "Régimen de Exportación",           # Zonas Francas / Exportadores
    "Retención a No Residentes",        # ISR retenciones (Art. 78)
    "Específico"                        # Otros casos específicos
]

async def seed_regimenes():
    print("🏛️ Iniciando carga de Regímenes Fiscales...")
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        insertados = 0
        saltados = 0

        for nombre_regimen in REGIMENES_FISCALES:
            # 1. Verificar si ya existe
            res = await session.execute(
                text("SELECT id FROM public.regimenes_fiscales WHERE nombre = :nombre"),
                {"nombre": nombre_regimen}
            )
            existente = res.scalar_one_or_none()

            if existente:
                print(f"   ⏭️  '{nombre_regimen}' ya existe.")
                saltados += 1
                continue

            # 2. Insertar nuevo registro con UUID aleatorio
            await session.execute(
                text("""
                    INSERT INTO public.regimenes_fiscales (id, nombre)
                    VALUES (gen_random_uuid(), :nombre)
                """),
                {"nombre": nombre_regimen}
            )
            print(f"   ✅ '{nombre_regimen}' insertado correctamente.")
            insertados += 1

        await session.commit()
        
        print("\n📊 Resumen:")
        print(f"   ✅ {insertados} regímenes insertados.")
        print(f"   ⏭️  {saltados} regímenes ya existentes.")
        print("✅ Proceso finalizado.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_regimenes())