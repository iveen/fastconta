"""
Script para poblar la tabla de categorias de activos fijos
con los limites legales del Articulo 28 del Decreto 10-2012.
Ejecutar: python -m app.scripts.seed_categorias_activos
"""
import asyncio
import os
import sys

from sqlalchemy import select

# Ajustar ruta para importar modelos desde la raíz del backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import AsyncSessionLocal
from app.models.global_models import CategoriaActivoFijo


async def seed():
    # Usar el contexto asíncrono de la sesión
    async with AsyncSessionLocal() as db:
        categorias = [
            {
                "nombre": "Edificios y Construcciones",
                "codigo_prefijo": "EDIF",
                "descripcion": "Edificios, construcciones e instalaciones adheridas a los inmuebles y sus mejoras. (Art. 28, numeral 1, Dec. 10-2012)",
                "tasa_minima_anual": 0.00,
                "tasa_maxima_anual": 5.00,
                "vida_util_meses_default": 240
            },
            {
                "nombre": "Plantaciones Agricolas",
                "codigo_prefijo": "PLAN",
                "descripcion": "Arboles, arbustos, frutales y especies vegetales que produzcan frutos o productos que generen rentas gravadas. (Art. 28, numeral 2, Dec. 10-2012)",
                "tasa_minima_anual": 0.00,
                "tasa_maxima_anual": 15.00,
                "vida_util_meses_default": 80
            },
            {
                "nombre": "Mobiliario y Equipo de Oficina",
                "codigo_prefijo": "MOB",
                "descripcion": "Instalaciones no adheridas a los inmuebles, mobiliario y equipo de oficina, buques-tanques, barcos y material ferroviario, maritimo, fluvial o lacustre. (Art. 28, numeral 3, Dec. 10-2012)",
                "tasa_minima_anual": 0.00,
                "tasa_maxima_anual": 20.00,
                "vida_util_meses_default": 60
            },
            {
                "nombre": "Maquinaria y Vehiculos",
                "codigo_prefijo": "VEH",
                "descripcion": "Semovientes utilizados como animales de carga o de trabajo, maquinaria, vehiculos en general, gruas, aviones, remolques, semirremolques, contenedores y material rodante. (Art. 28, numeral 4, Dec. 10-2012)",
                "tasa_minima_anual": 0.00,
                "tasa_maxima_anual": 20.00,
                "vida_util_meses_default": 60
            },
            {
                "nombre": "Equipo de Computo",
                "codigo_prefijo": "COMP",
                "descripcion": "Equipo de computacion, incluyendo los programas (software). (Art. 28, numeral 5, Dec. 10-2012)",
                "tasa_minima_anual": 0.00,
                "tasa_maxima_anual": 33.33,
                "vida_util_meses_default": 36
            },
            {
                "nombre": "Herramientas y Utensilios",
                "codigo_prefijo": "HERR",
                "descripcion": "Herramientas, porcelana, cristaleria, manteleria, cubiertos y similares. (Art. 28, numeral 6, Dec. 10-2012)",
                "tasa_minima_anual": 0.00,
                "tasa_maxima_anual": 25.00,
                "vida_util_meses_default": 48
            },
            {
                "nombre": "Ganado de Reproduccion",
                "codigo_prefijo": "GAN",
                "descripcion": "Reproductores de raza, machos y hembras. La depreciacion se calcula sobre el valor de costo de tales animales menos su valor como ganado comun. (Art. 28, numeral 7, Dec. 10-2012)",
                "tasa_minima_anual": 0.00,
                "tasa_maxima_anual": 25.00,
                "vida_util_meses_default": 48
            },
            {
                "nombre": "Otros Bienes Muebles",
                "codigo_prefijo": "OTRO",
                "descripcion": "Para los bienes muebles no indicados en los incisos anteriores. (Art. 28, numeral 8, Dec. 10-2012)",
                "tasa_minima_anual": 0.00,
                "tasa_maxima_anual": 10.00,
                "vida_util_meses_default": 120
            }
        ]
        
        print("🌱 Iniciando carga de categorias de activos fijos...")
        
        for cat_data in categorias:
            # Consulta asíncrona para verificar si ya existe
            stmt = select(CategoriaActivoFijo).where(CategoriaActivoFijo.nombre == cat_data["nombre"])
            result = await db.execute(stmt)
            existente = result.scalar_one_or_none()
            
            if existente:
                # Actualizar si ya existe
                for key, value in cat_data.items():
                    setattr(existente, key, value)
                print(f"  ✅ Actualizada: {cat_data['nombre']} (Max: {cat_data['tasa_maxima_anual']}%)")
            else:
                # Crear nueva
                nueva = CategoriaActivoFijo(**cat_data)
                db.add(nueva)
                print(f"  ➕ Creada: {cat_data['nombre']} (Max: {cat_data['tasa_maxima_anual']}%)")
        
        # Commit asíncrono
        await db.commit()
        print("\n✅ Carga de categorias completada exitosamente.")

if __name__ == "__main__":
    # Ejecutar el loop de eventos asíncrono
    asyncio.run(seed())