"""Service para Catálogo de Monedas"""
from uuid import UUID

from app.models.global_models import CatalogoMoneda
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession


class MonedaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def obtener_todos(
        self,
        activo: bool | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[CatalogoMoneda], int]:
        query = select(CatalogoMoneda)
        count_query = select(func.count()).select_from(CatalogoMoneda)

        if activo is not None:
            query = query.where(CatalogoMoneda.activo == activo)
            count_query = count_query.where(CatalogoMoneda.activo == activo)

        if search:
            filtro = or_(
                CatalogoMoneda.codigo_banguat.ilike(f"%{search}%"),
                CatalogoMoneda.codigo_iso.ilike(f"%{search}%"),
                CatalogoMoneda.nombre.ilike(f"%{search}%"),
            )
            query = query.where(filtro)
            count_query = count_query.where(filtro)

        total = (await self.db.execute(count_query)).scalar_one()
        query = query.order_by(CatalogoMoneda.codigo_iso).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def obtener_todos_activos(self) -> list[CatalogoMoneda]:
        query = (
            select(CatalogoMoneda)
            .where(CatalogoMoneda.activo.is_(True))
            .order_by(CatalogoMoneda.codigo_iso)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def obtener_por_id(self, moneda_id: UUID) -> CatalogoMoneda | None:
        query = select(CatalogoMoneda).where(CatalogoMoneda.id == moneda_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def crear(self, data: dict) -> CatalogoMoneda:
        existente = await self.db.execute(
            select(CatalogoMoneda).where(
                (CatalogoMoneda.codigo_banguat == data["codigo_banguat"]) |
                (CatalogoMoneda.codigo_iso == data["codigo_iso"])
            )
        )
        if existente.scalar_one_or_none():
            raise ValueError("Ya existe una moneda con ese código BANGUAT o ISO")

        moneda = CatalogoMoneda(**data)
        self.db.add(moneda)
        await self.db.commit()
        await self.db.refresh(moneda)
        return moneda

    async def actualizar(self, moneda_id: UUID, data: dict) -> CatalogoMoneda | None:
        moneda = await self.obtener_por_id(moneda_id)
        if not moneda:
            return None

        for campo, valor in data.items():
            setattr(moneda, campo, valor)

        await self.db.commit()
        await self.db.refresh(moneda)
        return moneda

    async def eliminar(self, moneda_id: UUID) -> bool:
        moneda = await self.obtener_por_id(moneda_id)
        if not moneda:
            return False
        moneda.activo = False
        await self.db.commit()
        return True