"""Service para Geografía (Departamentos y Municipios)"""
from uuid import UUID

from app.models.global_models import Departamento, Municipio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class GeografiaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # DEPARTAMENTOS
    # ============================================================
    async def obtener_departamentos(self) -> list[Departamento]:
        query = (
            select(Departamento)
            .options(selectinload(Departamento.municipios))  
            .order_by(Departamento.codigo_iso)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def obtener_departamento_por_id(self, depto_id: UUID) -> Departamento | None:
        query = (
            select(Departamento)
            .options(selectinload(Departamento.municipios))
            .where(Departamento.id == depto_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def crear_departamento(self, data: dict) -> Departamento:
        existente = await self.db.execute(
            select(Departamento).where(Departamento.codigo_iso == data["codigo_iso"])
        )
        if existente.scalar_one_or_none():
            raise ValueError(f"Ya existe un departamento con código '{data['codigo_iso']}'")

        depto = Departamento(**data)
        self.db.add(depto)
        await self.db.commit()
        await self.db.refresh(depto)
        return depto

    async def actualizar_departamento(self, depto_id: UUID, data: dict) -> Departamento | None:
        depto = await self.obtener_departamento_por_id(depto_id)
        if not depto:
            return None

        for campo, valor in data.items():
            setattr(depto, campo, valor)

        await self.db.commit()
        await self.db.refresh(depto)
        return depto

    async def eliminar_departamento(self, depto_id: UUID) -> bool:
        depto = await self.obtener_departamento_por_id(depto_id)
        if not depto:
            return False
        await self.db.delete(depto)
        await self.db.commit()
        return True

    # ============================================================
    # MUNICIPIOS
    # ============================================================
    async def obtener_municipios(self, departamento_id: UUID | None = None) -> list[Municipio]:
        query = select(Municipio).options(selectinload(Municipio.departamento))
        
        if departamento_id:
            query = query.where(Municipio.departamento_id == departamento_id)
        
        query = query.order_by(Municipio.codigo_iso)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def obtener_municipio_por_id(self, mun_id: UUID) -> Municipio | None:
        query = (
            select(Municipio)
            .options(selectinload(Municipio.departamento))
            .where(Municipio.id == mun_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def crear_municipio(self, data: dict) -> Municipio:
        existente = await self.db.execute(
            select(Municipio).where(Municipio.codigo_iso == data["codigo_iso"])
        )
        if existente.scalar_one_or_none():
            raise ValueError(f"Ya existe un municipio con código '{data['codigo_iso']}'")

        mun = Municipio(**data)
        self.db.add(mun)
        await self.db.commit()
        await self.db.refresh(mun)
        return mun

    async def actualizar_municipio(self, mun_id: UUID, data: dict) -> Municipio | None:
        mun = await self.obtener_municipio_por_id(mun_id)
        if not mun:
            return None

        for campo, valor in data.items():
            setattr(mun, campo, valor)

        await self.db.commit()
        await self.db.refresh(mun)
        return mun

    async def eliminar_municipio(self, mun_id: UUID) -> bool:
        mun = await self.obtener_municipio_por_id(mun_id)
        if not mun:
            return False
        await self.db.delete(mun)
        await self.db.commit()
        return True