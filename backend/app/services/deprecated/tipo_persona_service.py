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
        result = await self.db.execute(query)
        return [row[0] for row in result.all()]

    # ✅ AGREGAR ESTE MÉTODO QUE FALTABA
    async def obtener_todos_activos(self) -> list[TipoPersona]:
        """Obtiene todos los tipos de persona activos (para dropdowns)"""
        query = (
            select(TipoPersona)
            .where(TipoPersona.is_active.is_(True))  # Usa is_active por herencia de SoftDelete
            .order_by(TipoPersona.nombre)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

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