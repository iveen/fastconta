"""Service para Tipos de Persona"""
from logging import getLogger
from uuid import UUID

from app.models.global_models import TipoPersona
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = getLogger(__name__)


class TipoPersonaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def obtener_todos(self) -> list[TipoPersona]:
        query = select(TipoPersona).order_by(TipoPersona.nombre)
        
        print(f"🔥 SQL: {str(query.compile(compile_kwargs={'literal_binds': True}))}")
        
        result = await self.db.execute(query)
        
        # 🔥 PRUEBA 1: scalars().all() (original)
        print(f"🔥 PRUEBA 1 - scalars().all(): {len(result.scalars().all())} objetos")
        
        # 🔥 PRUEBA 2: all() sin scalars
        result2 = await self.db.execute(query)
        rows = result2.all()
        print(f"🔥 PRUEBA 2 - all(): {len(rows)} filas")
        if rows:
            print(f"🔥 Primera fila tipo: {type(rows[0])}")
            print(f"🔥 Primera fila: {rows[0]}")
        
        # 🔥 PRUEBA 3: iterar manualmente
        result3 = await self.db.execute(query)
        count = 0
        for row in result3:
            count += 1
            print(f"🔥 PRUEBA 3 - Fila {count}: {row}")
        print(f"🔥 PRUEBA 3 - Total iterando: {count}")
        
        # 🔥 PRUEBA 4: first()
        result4 = await self.db.execute(query)
        first = result4.scalars().first()
        print(f"🔥 PRUEBA 4 - first(): {first}")
        
        # Retornar usando el método que funcione
        result5 = await self.db.execute(query)
        return [row[0] for row in result5.all()]  # ← Usar all() en lugar de scalars()

    async def obtener_por_id(self, tipo_id: UUID) -> TipoPersona | None:
        query = select(TipoPersona).where(TipoPersona.id == tipo_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def crear(self, data: dict) -> TipoPersona:
        existente = await self.db.execute(
            select(TipoPersona).where(TipoPersona.nombre == data["nombre"])
        )
        if existente.scalar_one_or_none():
            raise ValueError(f"Ya existe un tipo de persona con nombre '{data['nombre']}'")

        tipo = TipoPersona(**data)
        self.db.add(tipo)
        await self.db.commit()
        await self.db.refresh(tipo)
        return tipo

    async def actualizar(self, tipo_id: UUID, data: dict) -> TipoPersona | None:
        tipo = await self.obtener_por_id(tipo_id)
        if not tipo:
            return None

        for campo, valor in data.items():
            setattr(tipo, campo, valor)

        await self.db.commit()
        await self.db.refresh(tipo)
        return tipo

    async def eliminar(self, tipo_id: UUID) -> bool:
        tipo = await self.obtener_por_id(tipo_id)
        if not tipo:
            return False
        await self.db.delete(tipo)
        await self.db.commit()
        return True