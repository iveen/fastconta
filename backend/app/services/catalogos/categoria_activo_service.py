"""Service para Categorías de Activos Fijos"""
from uuid import UUID

from app.models.global_models import CategoriaActivoFijo
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession


class CategoriaActivoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def obtener_todos(
        self,
        is_active: bool | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[CategoriaActivoFijo], int]:
        query = select(CategoriaActivoFijo)
        count_query = select(func.count()).select_from(CategoriaActivoFijo)

        if is_active is not None:
            query = query.where(CategoriaActivoFijo.is_active == is_active)
            count_query = count_query.where(CategoriaActivoFijo.is_active == is_active)

        if search:
            filtro = or_(
                CategoriaActivoFijo.nombre.ilike(f"%{search}%"),
                CategoriaActivoFijo.codigo_prefijo.ilike(f"%{search}%"),
                CategoriaActivoFijo.descripcion.ilike(f"%{search}%"),
            )
            query = query.where(filtro)
            count_query = count_query.where(filtro)

        total = (await self.db.execute(count_query)).scalar_one()
        query = query.order_by(CategoriaActivoFijo.nombre).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def obtener_todos_activos(self) -> list[CategoriaActivoFijo]:
        query = (
            select(CategoriaActivoFijo)
            .where(CategoriaActivoFijo.is_active.is_(True))
            .order_by(CategoriaActivoFijo.nombre)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def obtener_por_id(self, categoria_id: UUID) -> CategoriaActivoFijo | None:
        query = select(CategoriaActivoFijo).where(CategoriaActivoFijo.id == categoria_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def crear(self, data: dict) -> CategoriaActivoFijo:
        existente = await self.db.execute(
            select(CategoriaActivoFijo).where(
                (CategoriaActivoFijo.nombre == data["nombre"]) |
                (CategoriaActivoFijo.codigo_prefijo == data["codigo_prefijo"])
            )
        )
        if existente.scalar_one_or_none():
            raise ValueError("Ya existe una categoría con ese nombre o prefijo")

        categoria = CategoriaActivoFijo(**data)
        self.db.add(categoria)
        await self.db.commit()
        await self.db.refresh(categoria)
        return categoria

    async def actualizar(self, categoria_id: UUID, data: dict) -> CategoriaActivoFijo | None:
        categoria = await self.obtener_por_id(categoria_id)
        if not categoria:
            return None

        for campo, valor in data.items():
            setattr(categoria, campo, valor)

        await self.db.commit()
        await self.db.refresh(categoria)
        return categoria

    async def eliminar(self, categoria_id: UUID) -> bool:
        categoria = await self.obtener_por_id(categoria_id)
        if not categoria:
            return False
        categoria.is_active = False
        await self.db.commit()
        return True