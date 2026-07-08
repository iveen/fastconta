# app/scripts/seed_tipos_estados_libro.py
"""Seed para Tipos y Estados de Libro SAT"""
import asyncio
import os
import sys

from sqlalchemy import select

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import AsyncSessionLocal
from app.models.global_models import EstadoLibro, TipoLibro

TIPOS_LIBRO = [
    {"codigo": "compras", "nombre": "Libro de Compras"},
    {"codigo": "ventas", "nombre": "Libro de Ventas"},
]

ESTADOS_LIBRO = [
    {"nombre": "Borrador"},
    {"nombre": "Generado"},
    {"nombre": "Enviado"},
    {"nombre": "Aceptado"},
    {"nombre": "Rechazado"},
]


async def seed():
    async with AsyncSessionLocal() as db:
        print("🌱 Sembrando tipos de libro...")
        for data in TIPOS_LIBRO:
            stmt = select(TipoLibro).where(TipoLibro.codigo == data["codigo"])
            result = await db.execute(stmt)
            existente = result.scalar_one_or_none()
            if existente:
                print(f"  ✅ Ya existe: {data['codigo']}")
            else:
                db.add(TipoLibro(**data))
                print(f"  ➕ Creado: {data['codigo']}")

        print("\n Sembrando estados de libro...")
        for data in ESTADOS_LIBRO:
            stmt = select(EstadoLibro).where(EstadoLibro.nombre == data["nombre"])
            result = await db.execute(stmt)
            existente = result.scalar_one_or_none()
            if existente:
                print(f"  ✅ Ya existe: {data['nombre']}")
            else:
                db.add(EstadoLibro(**data))
                print(f"   Creado: {data['nombre']}")

        await db.commit()
        print("\n✅ Seed completado exitosamente.")


if __name__ == "__main__":
    asyncio.run(seed())