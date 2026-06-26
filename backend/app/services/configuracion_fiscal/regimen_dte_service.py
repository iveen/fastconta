"""Servicio para Configuración Régimen-DTE"""

from uuid import UUID

from app.models.global_models import RegimenDteConfig, RegimenFiscal, TipoDTE
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class RegimenDteService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # QUERIES
    # ============================================================
    async def obtener_por_regimen(
        self, regimen_id: UUID
    ) -> list[RegimenDteConfig]:
        """Lista DTE configurados para un régimen"""
        query = (
            select(RegimenDteConfig)
            .where(RegimenDteConfig.regimen_id == regimen_id)
            .options(
                selectinload(RegimenDteConfig.regimen),
                selectinload(RegimenDteConfig.dte),
            )
            .order_by(RegimenDteConfig.es_exclusivo.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def obtener_por_dte(self, dte_id: UUID) -> list[RegimenDteConfig]:
        """Lista regímenes configurados para un DTE"""
        query = (
            select(RegimenDteConfig)
            .where(RegimenDteConfig.dte_id == dte_id)
            .options(
                selectinload(RegimenDteConfig.regimen),
                selectinload(RegimenDteConfig.dte),
            )
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def obtener_configuracion(
        self, regimen_id: UUID, dte_id: UUID
    ) -> RegimenDteConfig | None:
        """Obtiene una configuración específica"""
        query = select(RegimenDteConfig).where(
            RegimenDteConfig.regimen_id == regimen_id,
            RegimenDteConfig.dte_id == dte_id,
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def obtener_dte_permitidos(
        self, regimen_id: UUID
    ) -> list[TipoDTE]:
        """Obtiene los DTE permitidos para un régimen (con info del DTE)"""
        query = (
            select(TipoDTE)
            .join(RegimenDteConfig, TipoDTE.id == RegimenDteConfig.dte_id)
            .where(
                RegimenDteConfig.regimen_id == regimen_id,
                TipoDTE.activo.is_(True),
            )
            .order_by(TipoDTE.codigo)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ============================================================
    # CRUD
    # ============================================================
    async def asociar(
        self,
        regimen_id: UUID,
        dte_id: UUID,
        es_exclusivo: bool = False,
    ) -> RegimenDteConfig:
        """Asocia un DTE a un régimen"""
        # Validar régimen activo
        regimen_query = select(RegimenFiscal).where(
            RegimenFiscal.id == regimen_id,
            RegimenFiscal.is_active.is_(True),
        )
        regimen_result = await self.db.execute(regimen_query)
        if regimen_result.scalars().first() is None:
            raise ValueError("Régimen no encontrado o inactivo")

        # Validar DTE activo
        dte_query = select(TipoDTE).where(
            TipoDTE.id == dte_id,
            TipoDTE.activo.is_(True),
        )
        dte_result = await self.db.execute(dte_query)
        if dte_result.scalars().first() is None:
            raise ValueError("Tipo DTE no encontrado o inactivo")

        # Verificar si ya existe
        existente = await self.obtener_configuracion(regimen_id, dte_id)
        if existente is not None:
            raise ValueError("El DTE ya está asociado al régimen")

        config = RegimenDteConfig(
            regimen_id=regimen_id,
            dte_id=dte_id,
            es_exclusivo=es_exclusivo,
        )
        self.db.add(config)
        await self.db.flush()
        await self.db.refresh(config)
        return config

    async def actualizar_configuracion(
        self,
        regimen_id: UUID,
        dte_id: UUID,
        es_exclusivo: bool | None = None,
    ) -> RegimenDteConfig | None:
        """Actualiza una configuración existente"""
        config = await self.obtener_configuracion(regimen_id, dte_id)
        if config is None:
            return None

        if es_exclusivo is not None:
            config.es_exclusivo = es_exclusivo

        await self.db.flush()
        await self.db.refresh(config)
        return config

    async def desasociar(self, regimen_id: UUID, dte_id: UUID) -> bool:
        """Elimina la asociación entre régimen y DTE"""
        config = await self.obtener_configuracion(regimen_id, dte_id)
        if config is None:
            return False

        await self.db.delete(config)
        await self.db.flush()
        return True

    async def asociar_bulk(
        self,
        regimen_id: UUID,
        dte_ids: list[UUID],
        es_exclusivo: bool = False,
    ) -> list[RegimenDteConfig]:
        """Asocia múltiples DTE a un régimen"""
        # Validar régimen
        regimen_query = select(RegimenFiscal).where(
            RegimenFiscal.id == regimen_id,
            RegimenFiscal.is_active.is_(True),
        )
        regimen_result = await self.db.execute(regimen_query)
        if regimen_result.scalars().first() is None:
            raise ValueError("Régimen no encontrado o inactivo")

        # Validar DTEs
        dte_query = select(TipoDTE).where(
            TipoDTE.id.in_(dte_ids),
            TipoDTE.activo.is_(True),
        )
        dte_result = await self.db.execute(dte_query)
        dtes_validos = dte_result.scalars().all()

        if len(dtes_validos) != len(dte_ids):
            raise ValueError("Algunos DTE no existen o están inactivos")

        # Crear asociaciones
        configs_creadas = []
        for dte_id in dte_ids:
            existente = await self.obtener_configuracion(regimen_id, dte_id)
            if existente is None:
                config = RegimenDteConfig(
                    regimen_id=regimen_id,
                    dte_id=dte_id,
                    es_exclusivo=es_exclusivo,
                )
                self.db.add(config)
                configs_creadas.append(config)

        await self.db.flush()
        return configs_creadas