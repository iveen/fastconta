"""
Servicio para gestión de tomas de inventario (cabecera).

Responsabilidades:
- CRUD de tomas (crear, listar, obtener, actualizar, eliminar)
- Cambio de estado (confirmar)
- Gestión de jobs asociados al eliminar una toma

NO gestiona items → eso lo hace ItemService.
"""
from typing import List
from uuid import UUID

from app.models.global_models import InventarioImportacionJob
from app.models.tenant_models import InventarioItem, InventarioToma
from app.schemas.inventario.toma import TomaCreate, TomaUpdate
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload


class TomaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def crear(
        self,
        tenant_id: int,
        data: TomaCreate,
        usuario_id: int | None = None,
    ) -> InventarioToma:
        """
        Crea una nueva toma de inventario.
        Valida unicidad por tenant + empresa + período fiscal.
        """
        stmt = select(InventarioToma).where(
            and_(
                InventarioToma.tenant_id == tenant_id,
                InventarioToma.empresa_id == data.empresa_id,
                InventarioToma.anio_periodo == data.anio_periodo,
                InventarioToma.mes_periodo == data.mes_periodo,
            )
        )
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise ValueError(
                f"Ya existe una toma para esta empresa en el período "
                f"{data.anio_periodo}/{str(data.mes_periodo).zfill(2)}"
            )

        toma = InventarioToma(
            tenant_id=tenant_id,
            created_by=usuario_id,
            updated_by=usuario_id,
            **data.model_dump(),
        )
        self.db.add(toma)
        await self.db.commit()
        await self.db.refresh(toma)
        return toma

    async def listar(
        self,
        tenant_id: int,
        empresa_id: int | None = None,
        estado: str | None = None,
        tipo: str | None = None,
        anio: int | None = None,
        mes: int | None = None,
    ) -> List[InventarioToma]:
        """Lista tomas con filtros opcionales, ordenadas por período descendente."""
        stmt = select(InventarioToma).where(
            InventarioToma.tenant_id == tenant_id
        )
        if empresa_id:
            stmt = stmt.where(InventarioToma.empresa_id == empresa_id)
        if estado:
            stmt = stmt.where(InventarioToma.estado == estado)
        if tipo:
            stmt = stmt.where(InventarioToma.tipo == tipo)
        if anio:
            stmt = stmt.where(InventarioToma.anio_periodo == anio)
        if mes:
            stmt = stmt.where(InventarioToma.mes_periodo == mes)

        stmt = stmt.order_by(
            InventarioToma.anio_periodo.desc(),
            InventarioToma.mes_periodo.desc(),
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def obtener_con_items(
        self,
        public_id: UUID,
        tenant_id: int,
    ) -> InventarioToma | None:
        """Obtiene una toma con todos sus items cargados (eager loading)."""
        stmt = (
            select(InventarioToma)
            .options(
                selectinload(InventarioToma.items)
                    .joinedload(InventarioItem.bodega),
                selectinload(InventarioToma.items)
                    .joinedload(InventarioItem.producto),
                joinedload(InventarioToma.empresa),
            )
            .where(
                and_(
                    InventarioToma.public_id == public_id,
                    InventarioToma.tenant_id == tenant_id,
                )
            )
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def actualizar(
        self,
        toma: InventarioToma,
        data: TomaUpdate,
        usuario_id: int | None = None,
    ) -> InventarioToma:
        """Actualiza datos de la toma. No permite modificar si está CONTABILIZADO."""
        if toma.estado == "CONTABILIZADO":
            raise ValueError("No se puede modificar una toma ya contabilizada")

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(toma, key, value)
        toma.updated_by = usuario_id
        await self.db.commit()
        await self.db.refresh(toma)
        return toma

    async def eliminar(self, toma: InventarioToma) -> None:
        """
        Elimina la toma y todos sus items (CASCADE).
        Solo si está en BORRADOR.
        
        ⚠️ IMPORTANTE: También marca como TOMA_ELIMINADA cualquier job
        PENDIENTE/PROCESANDO asociado a esta toma (tabla global).
        """
        if toma.estado != "BORRADOR":
            raise ValueError("Solo se pueden eliminar tomas en estado BORRADOR")

        # ✅ NUEVO: Marcar jobs asociados como TOMA_ELIMINADA
        await self._marcar_jobs_como_eliminados(toma.id)

        await self.db.delete(toma)
        await self.db.commit()

    async def _marcar_jobs_como_eliminados(self, toma_id: int) -> None:
        """
        Marca jobs globales asociados a una toma como TOMA_ELIMINADA.
        
        La tabla InventarioImportacionJob está en schema public (global),
        por lo que no necesita cambio de search_path.
        """
        from datetime import datetime, timezone

        stmt_update = (
            update(InventarioImportacionJob)
            .where(
                and_(
                    InventarioImportacionJob.toma_id == toma_id,
                    InventarioImportacionJob.estado.in_(
                        ["PENDIENTE", "PROCESANDO"]
                    ),
                )
            )
            .values(
                estado="TOMA_ELIMINADA",
                mensaje_error="La toma de inventario fue eliminada",
                finalizado_en=datetime.now(timezone.utc),
            )
        )
        await self.db.execute(stmt_update)

    async def confirmar(
        self,
        toma: InventarioToma,
        usuario_id: int | None = None,
    ) -> InventarioToma:
        """
        Confirma una toma (cambia estado a CONFIRMADO).
        Requiere: estado BORRADOR + al menos un item.
        """
        if toma.estado != "BORRADOR":
            raise ValueError("Solo se pueden confirmar tomas en estado BORRADOR")

        # Verificar que tenga items (consulta directa por si no vienen cargados)
        stmt_items = select(InventarioItem.id).where(
            InventarioItem.toma_id == toma.id
        ).limit(1)
        result = await self.db.execute(stmt_items)
        if not result.scalar_one_or_none():
            raise ValueError("No se puede confirmar una toma sin items")

        toma.estado = "CONFIRMADO"
        toma.updated_by = usuario_id
        await self.db.commit()
        await self.db.refresh(toma)
        return toma