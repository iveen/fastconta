"""
Servicio para gestión de jobs de importación (monitoreo global).

Responsabilidades:
- Consultar estado de jobs
- Cancelar jobs pendientes
- Monitoreo global para superadmin
"""
from typing import List

from app.models.global_models import InventarioImportacionJob
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession


class JobService:
    """
    Servicio para gestión de jobs de importación.
    
    Los jobs están en schema public (global), por lo que este servicio
    no requiere cambio de search_path.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def obtener_por_id(
        self, job_id: int
    ) -> InventarioImportacionJob | None:
        """Obtiene un job por su ID interno."""
        return await self.db.get(InventarioImportacionJob, job_id)

    async def obtener_por_public_id(
        self, public_id: str
    ) -> InventarioImportacionJob | None:
        """Obtiene un job por su public_id (UUID)."""
        stmt = select(InventarioImportacionJob).where(
            InventarioImportacionJob.public_id == public_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def listar_por_usuario(
        self,
        usuario_id: int,
        tenant_id: int,
        limit: int = 20,
    ) -> List[InventarioImportacionJob]:
        """Lista los jobs recientes de un usuario en un tenant."""
        stmt = (
            select(InventarioImportacionJob)
            .where(
                and_(
                    InventarioImportacionJob.tenant_id == tenant_id,
                    InventarioImportacionJob.usuario_id == usuario_id,
                )
            )
            .order_by(InventarioImportacionJob.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def listar_por_toma(
        self,
        toma_id: int,
        tenant_id: int,
    ) -> List[InventarioImportacionJob]:
        """Lista todos los jobs de una toma específica."""
        stmt = (
            select(InventarioImportacionJob)
            .where(
                and_(
                    InventarioImportacionJob.tenant_id == tenant_id,
                    InventarioImportacionJob.toma_id == toma_id,
                )
            )
            .order_by(InventarioImportacionJob.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def listar_global(
        self,
        tenant_id: int | None = None,
        estado: str | None = None,
        limit: int = 100,
    ) -> List[InventarioImportacionJob]:
        """
        Lista jobs globales (para superadmin).
        
        Args:
            tenant_id: Filtrar por tenant (opcional)
            estado: Filtrar por estado (opcional)
            limit: Máximo de resultados
        """
        stmt = select(InventarioImportacionJob)
        if tenant_id:
            stmt = stmt.where(InventarioImportacionJob.tenant_id == tenant_id)
        if estado:
            stmt = stmt.where(InventarioImportacionJob.estado == estado)
        stmt = stmt.order_by(
            InventarioImportacionJob.created_at.desc()
        ).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def cancelar(
        self,
        job: InventarioImportacionJob,
        usuario_id: int,
    ) -> InventarioImportacionJob:
        """
        Cancela un job PENDIENTE.
        
        Solo se pueden cancelar jobs que aún no han empezado a procesarse.
        Si ya está PROCESANDO, no se puede cancelar (ya hay datos insertados).
        """
        if job.estado != "PENDIENTE":
            raise ValueError(
                f"Solo se pueden cancelar jobs PENDIENTES. "
                f"Estado actual: {job.estado}"
            )

        job.estado = "CANCELADO"
        job.mensaje_error = "Cancelado por el usuario"
        job.updated_by = usuario_id
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def obtener_estadisticas(
        self, tenant_id: int | None = None
    ) -> dict:
        """
        Obtiene estadísticas globales de jobs.
        
        Returns:
            dict con conteos por estado
        """
        from sqlalchemy import func

        stmt = select(
            InventarioImportacionJob.estado,
            func.count(InventarioImportacionJob.id),
        )
        if tenant_id:
            stmt = stmt.where(
                InventarioImportacionJob.tenant_id == tenant_id
            )
        stmt = stmt.group_by(InventarioImportacionJob.estado)
        result = await self.db.execute(stmt)

        estadisticas = {estado: count for estado, count in result.all()}
        return {
            "pendientes": estadisticas.get("PENDIENTE", 0),
            "procesando": estadisticas.get("PROCESANDO", 0),
            "completados": estadisticas.get("COMPLETADO", 0),
            "fallidos": estadisticas.get("FALLIDO", 0),
            "cancelados": estadisticas.get("CANCELADO", 0),
            "toma_eliminada": estadisticas.get("TOMA_ELIMINADA", 0),
            "total": sum(estadisticas.values()),
        }