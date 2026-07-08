"""Service para Configuración Régimen-DTE"""
from uuid import UUID

from app.models.global_models import RegimenDteConfig, RegimenFiscal, TipoDTE
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class RegimenDteService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # LISTAR POR RÉGIMEN (con datos enriquecidos)
    # ============================================================
    async def obtener_por_regimen(self, regimen_id: UUID) -> list[dict]:
        query = (
            select(RegimenDteConfig)
            .options(
                selectinload(RegimenDteConfig.regimen),
                selectinload(RegimenDteConfig.dte),
            )
            .where(RegimenDteConfig.regimen_id == regimen_id)
        )
        result = await self.db.execute(query)
        configs = result.scalars().all()

        return [
            {
                "id": c.id,
                "regimen_id": c.regimen_id,
                "dte_id": c.dte_id,
                "es_exclusivo": c.es_exclusivo,
                "regimen_codigo": c.regimen.codigo if c.regimen else None,
                "regimen_nombre": c.regimen.nombre if c.regimen else None,
                "dte_codigo": c.dte.codigo if c.dte else None,
                "dte_descripcion": c.dte.descripcion if c.dte else None,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
                "created_by": c.created_by,
                "updated_by": c.updated_by,
            }
            for c in configs
        ]

    # ============================================================
    # LISTAR POR DTE (con datos enriquecidos)
    # ============================================================
    async def obtener_por_dte(self, dte_id: UUID) -> list[dict]:
        query = (
            select(RegimenDteConfig)
            .options(
                selectinload(RegimenDteConfig.regimen),
                selectinload(RegimenDteConfig.dte),
            )
            .where(RegimenDteConfig.dte_id == dte_id)
        )
        result = await self.db.execute(query)
        configs = result.scalars().all()

        return [
            {
                "id": c.id,
                "regimen_id": c.regimen_id,
                "dte_id": c.dte_id,
                "es_exclusivo": c.es_exclusivo,
                "regimen_codigo": c.regimen.codigo if c.regimen else None,
                "regimen_nombre": c.regimen.nombre if c.regimen else None,
                "dte_codigo": c.dte.codigo if c.dte else None,
                "dte_descripcion": c.dte.descripcion if c.dte else None,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
                "created_by": c.created_by,
                "updated_by": c.updated_by,
            }
            for c in configs
        ]

    # ============================================================
    # DTE PERMITIDOS PARA RÉGIMEN
    # ============================================================
    async def obtener_dte_permitidos(self, regimen_id: UUID) -> list[dict]:
        query = (
            select(TipoDTE)
            .join(RegimenDteConfig, RegimenDteConfig.dte_id == TipoDTE.id)
            .where(RegimenDteConfig.regimen_id == regimen_id)
            .where(TipoDTE.activo.is_(True))
            .order_by(TipoDTE.codigo)
        )
        result = await self.db.execute(query)
        dtes = result.scalars().all()
        return [
            {"id": d.id, "codigo": d.codigo, "descripcion": d.descripcion}
            for d in dtes
        ]

    # ============================================================
    # ASOCIAR UN DTE A UN RÉGIMEN
    # ============================================================
    async def asociar(
        self, regimen_id: UUID, dte_id: UUID, es_exclusivo: bool = False
    ) -> RegimenDteConfig:
        regimen = await self.db.get(RegimenFiscal, regimen_id)
        if not regimen:
            raise ValueError("Régimen fiscal no encontrado")

        dte = await self.db.get(TipoDTE, dte_id)
        if not dte:
            raise ValueError("Tipo DTE no encontrado")

        existente = await self.db.execute(
            select(RegimenDteConfig).where(
                and_(
                    RegimenDteConfig.regimen_id == regimen_id,
                    RegimenDteConfig.dte_id == dte_id,
                )
            )
        )
        if existente.scalar_one_or_none():
            raise ValueError("Esta asociación ya existe")

        config = RegimenDteConfig(
            regimen_id=regimen_id,
            dte_id=dte_id,
            es_exclusivo=es_exclusivo,
        )
        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        return config

    # ============================================================
    # ACTUALIZAR CONFIGURACIÓN
    # ============================================================
    async def actualizar_configuracion(
        self, regimen_id: UUID, dte_id: UUID, es_exclusivo: bool
    ) -> RegimenDteConfig | None:
        query = select(RegimenDteConfig).where(
            and_(
                RegimenDteConfig.regimen_id == regimen_id,
                RegimenDteConfig.dte_id == dte_id,
            )
        )
        result = await self.db.execute(query)
        config = result.scalar_one_or_none()
        if not config:
            return None

        config.es_exclusivo = es_exclusivo
        await self.db.commit()
        await self.db.refresh(config)
        return config

    # ============================================================
    # DESASOCIAR
    # ============================================================
    async def desasociar(self, regimen_id: UUID, dte_id: UUID) -> bool:
        query = delete(RegimenDteConfig).where(
            and_(
                RegimenDteConfig.regimen_id == regimen_id,
                RegimenDteConfig.dte_id == dte_id,
            )
        )
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount > 0

    # ============================================================
    # ASOCIACIÓN MASIVA (bulk)
    # ============================================================
    async def asociar_bulk(
        self, regimen_id: UUID, dte_ids: list[UUID], es_exclusivo: bool = False
    ) -> list[RegimenDteConfig]:
        regimen = await self.db.get(RegimenFiscal, regimen_id)
        if not regimen:
            raise ValueError("Régimen fiscal no encontrado")

        existentes_query = select(RegimenDteConfig.dte_id).where(
            RegimenDteConfig.regimen_id == regimen_id
        )
        existentes_result = await self.db.execute(existentes_query)
        existentes = set(existentes_result.scalars().all())

        configs = []
        for dte_id in dte_ids:
            if dte_id in existentes:
                continue

            dte = await self.db.get(TipoDTE, dte_id)
            if not dte:
                raise ValueError(f"Tipo DTE con id {dte_id} no encontrado")

            config = RegimenDteConfig(
                regimen_id=regimen_id,
                dte_id=dte_id,
                es_exclusivo=es_exclusivo,
            )
            self.db.add(config)
            configs.append(config)

        await self.db.commit()
        for c in configs:
            await self.db.refresh(c)
        return configs