"""Servicio para gestión de Reglas de Filtrado y Exclusiones"""

from uuid import UUID

from app.models.global_models import (
    CasillaSat,
    ExclusionCasilla,
    ReglaFiltradoFactura,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class ReglaFiltradoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # QUERIES - REGLAS
    # ============================================================
    async def obtener_reglas_por_casilla(
        self, casilla_id: UUID
    ) -> list[ReglaFiltradoFactura]:
        """Lista reglas de filtrado de una casilla"""
        query = (
            select(ReglaFiltradoFactura)
            .where(ReglaFiltradoFactura.casilla_id == casilla_id)
            .order_by(ReglaFiltradoFactura.orden)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def obtener_regla_por_id(
        self, regla_id: UUID
    ) -> ReglaFiltradoFactura | None:
        """Obtiene una regla específica"""
        query = select(ReglaFiltradoFactura).where(
            ReglaFiltradoFactura.id == regla_id
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def obtener_todas_reglas(
        self,
        casilla_id: UUID | None = None,
        es_activa: bool | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[ReglaFiltradoFactura], int]:
        """Lista todas las reglas con filtros"""
        query = select(ReglaFiltradoFactura)

        if casilla_id is not None:
            query = query.where(ReglaFiltradoFactura.casilla_id == casilla_id)
        if es_activa is not None:
            query = query.where(ReglaFiltradoFactura.es_activa.is_(es_activa))

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.order_by(ReglaFiltradoFactura.nombre).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    # ============================================================
    # CRUD - REGLAS
    # ============================================================
    async def crear_regla(self, data: dict) -> ReglaFiltradoFactura:
        """Crea una nueva regla de filtrado"""
        # Validar que la casilla existe
        casilla_query = select(CasillaSat).where(CasillaSat.id == data["casilla_id"])
        casilla_result = await self.db.execute(casilla_query)
        if casilla_result.scalars().first() is None:
            raise ValueError("Casilla no encontrada")

        regla = ReglaFiltradoFactura(**data)
        self.db.add(regla)
        await self.db.flush()
        await self.db.refresh(regla)
        return regla

    async def actualizar_regla(
        self, regla_id: UUID, data: dict
    ) -> ReglaFiltradoFactura | None:
        """Actualiza una regla"""
        regla = await self.obtener_regla_por_id(regla_id)
        if regla is None:
            return None

        for key, value in data.items():
            if hasattr(regla, key):
                setattr(regla, key, value)

        await self.db.flush()
        await self.db.refresh(regla)
        return regla

    async def eliminar_regla(self, regla_id: UUID) -> bool:
        """Elimina una regla"""
        regla = await self.obtener_regla_por_id(regla_id)
        if regla is None:
            return False

        await self.db.delete(regla)
        await self.db.flush()
        return True

    # ============================================================
    # QUERIES - EXCLUSIONES
    # ============================================================
    async def obtener_exclusiones_por_casilla(
        self, casilla_id: UUID
    ) -> list[ExclusionCasilla]:
        """Lista exclusiones de una casilla"""
        query = (
            select(ExclusionCasilla)
            .where(ExclusionCasilla.casilla_id == casilla_id)
            .order_by(ExclusionCasilla.nombre)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def obtener_exclusion_por_id(
        self, exclusion_id: UUID
    ) -> ExclusionCasilla | None:
        """Obtiene una exclusión específica"""
        query = select(ExclusionCasilla).where(
            ExclusionCasilla.id == exclusion_id
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def obtener_todas_exclusiones(
        self,
        casilla_id: UUID | None = None,
        es_activa: bool | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[ExclusionCasilla], int]:
        """Lista todas las exclusiones con filtros"""
        query = select(ExclusionCasilla)

        if casilla_id is not None:
            query = query.where(ExclusionCasilla.casilla_id == casilla_id)
        if es_activa is not None:
            query = query.where(ExclusionCasilla.es_activa.is_(es_activa))

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.order_by(ExclusionCasilla.nombre).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    # ============================================================
    # CRUD - EXCLUSIONES
    # ============================================================
    async def crear_exclusion(self, data: dict) -> ExclusionCasilla:
        """Crea una nueva exclusión"""
        # Validar que la casilla existe
        casilla_query = select(CasillaSat).where(CasillaSat.id == data["casilla_id"])
        casilla_result = await self.db.execute(casilla_query)
        if casilla_result.scalars().first() is None:
            raise ValueError("Casilla no encontrada")

        exclusion = ExclusionCasilla(**data)
        self.db.add(exclusion)
        await self.db.flush()
        await self.db.refresh(exclusion)
        return exclusion

    async def actualizar_exclusion(
        self, exclusion_id: UUID, data: dict
    ) -> ExclusionCasilla | None:
        """Actualiza una exclusión"""
        exclusion = await self.obtener_exclusion_por_id(exclusion_id)
        if exclusion is None:
            return None

        for key, value in data.items():
            if hasattr(exclusion, key):
                setattr(exclusion, key, value)

        await self.db.flush()
        await self.db.refresh(exclusion)
        return exclusion

    async def eliminar_exclusion(self, exclusion_id: UUID) -> bool:
        """Elimina una exclusión"""
        exclusion = await self.obtener_exclusion_por_id(exclusion_id)
        if exclusion is None:
            return False

        await self.db.delete(exclusion)
        await self.db.flush()
        return True

    # ============================================================
    # CONFIGURACIÓN COMPLETA DE CASILLA
    # ============================================================
    async def obtener_configuracion_casilla(
        self, casilla_id: UUID
    ) -> dict | None:
        """Obtiene la configuración completa de una casilla (reglas + exclusiones)"""
        # Obtener casilla
        casilla_query = (
            select(CasillaSat)
            .where(CasillaSat.id == casilla_id)
            .options(
                selectinload(CasillaSat.reglas_filtrado),
                selectinload(CasillaSat.exclusiones),
            )
        )
        casilla_result = await self.db.execute(casilla_query)
        casilla = casilla_result.scalars().first()

        if casilla is None:
            return None

        return {
            "casilla_id": casilla.id,
            "casilla_codigo": casilla.codigo,
            "casilla_nombre": casilla.nombre,
            "reglas": casilla.reglas_filtrado,
            "exclusiones": casilla.exclusiones,
            "total_reglas": len(casilla.reglas_filtrado),
            "total_exclusiones": len(casilla.exclusiones),
        }