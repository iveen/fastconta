"""Service para Actividades Económicas SAT"""
from uuid import UUID

from app.models.global_models import ActividadEconomicaSAT
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession


class ActividadEconomicaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def obtener_todos(
        self,
        activa: bool | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[ActividadEconomicaSAT], int]:
        query = select(ActividadEconomicaSAT)
        count_query = select(func.count()).select_from(ActividadEconomicaSAT)

        if activa is not None:
            query = query.where(ActividadEconomicaSAT.activa == activa)
            count_query = count_query.where(ActividadEconomicaSAT.activa == activa)

        if search:
            filtro = or_(
                ActividadEconomicaSAT.codigo_sat.ilike(f"%{search}%"),
                ActividadEconomicaSAT.nombre_actividad.ilike(f"%{search}%"),
                ActividadEconomicaSAT.seccion.ilike(f"%{search}%"),
            )
            query = query.where(filtro)
            count_query = count_query.where(filtro)

        total = (await self.db.execute(count_query)).scalar_one()
        query = query.order_by(ActividadEconomicaSAT.codigo_sat).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def obtener_todos_activas(self) -> list[ActividadEconomicaSAT]:
        query = (
            select(ActividadEconomicaSAT)
            .where(ActividadEconomicaSAT.active.is_(True))
            .order_by(ActividadEconomicaSAT.codigo_sat)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def obtener_por_id(self, actividad_id: UUID) -> ActividadEconomicaSAT | None:
        query = select(ActividadEconomicaSAT).where(ActividadEconomicaSAT.id == actividad_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def crear(self, data: dict) -> ActividadEconomicaSAT:
        existente = await self.db.execute(
            select(ActividadEconomicaSAT).where(
                ActividadEconomicaSAT.codigo_sat == data["codigo_sat"]
            )
        )
        if existente.scalar_one_or_none():
            raise ValueError(f"Ya existe una actividad con código SAT '{data['codigo_sat']}'")

        actividad = ActividadEconomicaSAT(**data)
        self.db.add(actividad)
        await self.db.commit()
        await self.db.refresh(actividad)
        return actividad

    async def actualizar(self, actividad_id: UUID, data: dict) -> ActividadEconomicaSAT | None:
        actividad = await self.obtener_por_id(actividad_id)
        if not actividad:
            return None

        for campo, valor in data.items():
            setattr(actividad, campo, valor)

        await self.db.commit()
        await self.db.refresh(actividad)
        return actividad

    async def eliminar(self, actividad_id: UUID) -> bool:
        actividad = await self.obtener_por_id(actividad_id)
        if not actividad:
            return False
        actividad.activa = False
        await self.db.commit()
        return True