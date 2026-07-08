"""Servicio para gestión de Tipos de Persona"""

from uuid import UUID

from app.models.global_models import TipoPersona
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class TipoPersonaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # QUERIES
    # ============================================================
    async def obtener_todos(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[TipoPersona], int]:
        """Lista todos los tipos de persona"""
        query = select(TipoPersona)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.order_by(TipoPersona.nombre).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def obtener_por_id(self, tipo_id: UUID) -> TipoPersona | None:
        """Obtiene un tipo de persona por ID"""
        query = select(TipoPersona).where(TipoPersona.id == tipo_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def obtener_por_nombre(self, nombre: str) -> TipoPersona | None:
        """Obtiene un tipo de persona por nombre"""
        query = select(TipoPersona).where(TipoPersona.nombre == nombre)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def obtener_todos_lista(self) -> list[TipoPersona]:
        """Obtiene todos los tipos (sin paginación, para dropdowns)"""
        query = select(TipoPersona).order_by(TipoPersona.nombre)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ============================================================
    # CRUD
    # ============================================================
    async def crear(self, data: dict) -> TipoPersona:
        """Crea un nuevo tipo de persona"""
        # Validar nombre único
        existente = await self.obtener_por_nombre(data["nombre"])
        if existente is not None:
            raise ValueError(f"Ya existe un tipo de persona con nombre '{data['nombre']}'")

        tipo = TipoPersona(**data)
        self.db.add(tipo)
        await self.db.flush()
        await self.db.refresh(tipo)
        return tipo

    async def actualizar(
        self, tipo_id: UUID, data: dict
    ) -> TipoPersona | None:
        """Actualiza un tipo de persona"""
        tipo = await self.obtener_por_id(tipo_id)
        if tipo is None:
            return None

        # Validar nombre único si cambia
        if "nombre" in data and data["nombre"] != tipo.nombre:
            existente = await self.obtener_por_nombre(data["nombre"])
            if existente is not None:
                raise ValueError(
                    f"Ya existe un tipo de persona con nombre '{data['nombre']}'"
                )

        for key, value in data.items():
            if hasattr(tipo, key):
                setattr(tipo, key, value)

        await self.db.flush()
        await self.db.refresh(tipo)
        return tipo

    async def eliminar(self, tipo_id: UUID) -> bool:
        """Elimina un tipo de persona"""
        tipo = await self.obtener_por_id(tipo_id)
        if tipo is None:
            return False

        await self.db.delete(tipo)
        await self.db.flush()
        return True