"""Servicio para gestión de Secciones de Formulario SAT"""

from uuid import UUID

from app.models.global_models import FormularioSat, SeccionFormulario
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class SeccionFormularioService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # QUERIES
    # ============================================================
    async def obtener_por_formulario(
        self,
        formulario_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[SeccionFormulario], int]:
        """Lista secciones de un formulario ordenadas"""
        query = (
            select(SeccionFormulario)
            .where(SeccionFormulario.formulario_id == formulario_id)
            .options(selectinload(SeccionFormulario.casillas))
            .order_by(SeccionFormulario.orden)
        )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        secciones = result.scalars().all()

        return list(secciones), total

    async def obtener_por_id(self, seccion_id: UUID) -> SeccionFormulario | None:
        """Obtiene una sección con sus casillas"""
        query = (
            select(SeccionFormulario)
            .where(SeccionFormulario.id == seccion_id)
            .options(selectinload(SeccionFormulario.casillas))
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    # ============================================================
    # CRUD
    # ============================================================
    async def crear(
        self, data: dict, usuario_id: UUID | None = None
    ) -> SeccionFormulario:
        """Crea una nueva sección"""
        # Validar que el formulario existe
        form_query = select(FormularioSat).where(
            FormularioSat.id == data["formulario_id"]
        )
        form_result = await self.db.execute(form_query)
        if form_result.scalars().first() is None:
            raise ValueError("Formulario no encontrado")

        seccion = SeccionFormulario(**data, created_by=usuario_id)
        self.db.add(seccion)
        await self.db.flush()
        await self.db.refresh(seccion)
        return seccion

    async def actualizar(
        self,
        seccion_id: UUID,
        data: dict,
        usuario_id: UUID | None = None,
    ) -> SeccionFormulario | None:
        """Actualiza una sección"""
        seccion = await self.obtener_por_id(seccion_id)
        if seccion is None:
            return None

        for key, value in data.items():
            if hasattr(seccion, key):
                setattr(seccion, key, value)

        seccion.updated_by = usuario_id
        await self.db.flush()
        await self.db.refresh(seccion)
        return seccion

    async def eliminar(self, seccion_id: UUID) -> bool:
        """Elimina una sección (hard delete con cascade)"""
        seccion = await self.obtener_por_id(seccion_id)
        if seccion is None:
            return False

        await self.db.delete(seccion)
        await self.db.flush()
        return True

    # ============================================================
    # REORDENAR
    # ============================================================
    async def reordenar(
        self,
        formulario_id: UUID,
        orden_secciones: list[UUID],
        usuario_id: UUID | None = None,
    ) -> bool:
        """Reordena las secciones de un formulario"""
        # Validar que todas las secciones pertenecen al formulario
        query = select(SeccionFormulario).where(
            SeccionFormulario.formulario_id == formulario_id,
            SeccionFormulario.id.in_(orden_secciones),
        )
        result = await self.db.execute(query)
        secciones_existentes = result.scalars().all()

        if len(secciones_existentes) != len(orden_secciones):
            raise ValueError("Algunas secciones no pertenecen al formulario")

        # Actualizar orden
        for idx, seccion_id in enumerate(orden_secciones):
            seccion = next(s for s in secciones_existentes if s.id == seccion_id)
            seccion.orden = idx
            seccion.updated_by = usuario_id

        await self.db.flush()
        return True