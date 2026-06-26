"""Seed para Tipos de Persona"""

import asyncio
import uuid

from app.db.session import AsyncSessionLocal
from app.models.global_models import TipoPersona


async def seed_tipos_persona():
    """Crea los tipos de persona básicos"""
    async with AsyncSessionLocal() as db:
        try:
            # Verificar si ya existen
            from sqlalchemy import select
            result = await db.execute(select(TipoPersona))
            existentes = result.scalars().all()
            
            if existentes:
                print("⚠️  Ya existen tipos de persona en la base de datos")
                return
            
            # Tipos de persona estándar
            tipos_data = [
                {"nombre": "NATURAL"},
                {"nombre": "JURIDICA"},
            ]
            
            for tipo_data in tipos_data:
                tipo = TipoPersona(id=uuid.uuid4(), **tipo_data)
                db.add(tipo)
            
            await db.commit()
            print("✅ Seed de tipos de persona completado")
            print(f"   - {len(tipos_data)} tipos creados")
            
        except Exception as e:
            await db.rollback()
            print(f" Error ejecutando seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_tipos_persona())