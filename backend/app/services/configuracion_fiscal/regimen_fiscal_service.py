"""Servicio para gestión de Regímenes Fiscales"""

from uuid import UUID

from app.models.global_models import FormularioSat, RegimenFiscal, RegimenFormularioSat
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class RegimenFiscalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # QUERIES
    # ============================================================

    async def obtener_todos(
        self,
        is_active: bool | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[RegimenFiscal], int]:
        """Lista regímenes fiscales con filtros"""
        query = select(RegimenFiscal)

        if is_active is not None:
            query = query.where(RegimenFiscal.is_active.is_(is_active))

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (RegimenFiscal.codigo.ilike(search_pattern))
                | (RegimenFiscal.nombre.ilike(search_pattern))
                | (RegimenFiscal.descripcion.ilike(search_pattern))
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.order_by(RegimenFiscal.codigo).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def obtener_por_id(self, regimen_id: UUID) -> RegimenFiscal | None:
        """Obtiene un régimen fiscal por ID"""
        query = select(RegimenFiscal).where(RegimenFiscal.id == regimen_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def obtener_por_codigo(self, codigo: str) -> RegimenFiscal | None:
        """Obtiene un régimen fiscal por código"""
        query = select(RegimenFiscal).where(RegimenFiscal.codigo == codigo)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def obtener_todos_lista(self) -> list[RegimenFiscal]:
        """Obtiene todos los regímenes (sin paginación, para dropdowns)"""
        query = (
            select(RegimenFiscal)
            .where(RegimenFiscal.is_active.is_(True))
            .order_by(RegimenFiscal.codigo)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def obtener_formularios_asociados(self, regimen_id: UUID) -> list[dict]:
        """
        Obtiene los formularios SAT asociados a un régimen,
        incluyendo si es obligatorio o no.
        """
        query = (
            select(
                FormularioSat.id,
                FormularioSat.codigo,
                FormularioSat.version,
                FormularioSat.nombre,
                RegimenFormularioSat.es_obligatorio,
            )
            .join(
                RegimenFormularioSat,
                RegimenFormularioSat.formulario_id == FormularioSat.id,
            )
            .where(RegimenFormularioSat.regimen_id == regimen_id)
            .order_by(FormularioSat.codigo)
        )
        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "id": row.id,
                "codigo": row.codigo,
                "version": row.version,
                "nombre": row.nombre,
                "es_obligatorio": row.es_obligatorio,
            }
            for row in rows
        ]

    # ============================================================
    # CRUD
    # ============================================================

    async def crear(self, data: dict) -> RegimenFiscal:
        """Crea un nuevo régimen fiscal"""
        # Validar código único
        existente = await self.obtener_por_codigo(data["codigo"])
        if existente is not None:
            raise ValueError(f"Ya existe un régimen con código '{data['codigo']}'")

        regimen = RegimenFiscal(**data)
        self.db.add(regimen)
        await self.db.flush()
        await self.db.refresh(regimen)
        return regimen

    async def actualizar(
        self, regimen_id: UUID, data: dict
    ) -> RegimenFiscal | None:
        """Actualiza un régimen fiscal"""
        regimen = await self.obtener_por_id(regimen_id)
        if regimen is None:
            return None

        for key, value in data.items():
            if hasattr(regimen, key):
                setattr(regimen, key, value)

        await self.db.flush()
        await self.db.refresh(regimen)
        return regimen

    async def eliminar(self, regimen_id: UUID) -> bool:
        """Soft delete (is_active = False)"""
        regimen = await self.obtener_por_id(regimen_id)
        if regimen is None:
            return False

        regimen.is_active = False
        await self.db.flush()
        return True