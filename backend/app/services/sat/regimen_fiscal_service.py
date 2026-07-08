"""Service para Regímenes Fiscales"""
from uuid import UUID

from app.models.global_models import FormularioSat, RegimenFiscal, RegimenFormularioSat
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession


class RegimenFiscalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------------------------------------------------------------
    # LISTAR CON PAGINACIÓN Y FILTROS
    # ---------------------------------------------------------------
    async def obtener_todos(
        self,
        is_active: bool | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[RegimenFiscal], int]:
        query = select(RegimenFiscal)
        count_query = select(func.count()).select_from(RegimenFiscal)

        if is_active is not None:
            query = query.where(RegimenFiscal.is_active == is_active)
            count_query = count_query.where(RegimenFiscal.is_active == is_active)

        if search:
            filtro = or_(
                RegimenFiscal.codigo.ilike(f"%{search}%"),
                RegimenFiscal.nombre.ilike(f"%{search}%"),
                RegimenFiscal.descripcion.ilike(f"%{search}%"),
            )
            query = query.where(filtro)
            count_query = count_query.where(filtro)

        total = (await self.db.execute(count_query)).scalar_one()
        query = query.order_by(RegimenFiscal.codigo).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    # ---------------------------------------------------------------
    # LISTAR ACTIVOS (sin paginación, para dropdowns)
    # ---------------------------------------------------------------
    async def obtener_todos_lista(self) -> list[RegimenFiscal]:
        query = (
            select(RegimenFiscal)
            .where(RegimenFiscal.is_active.is_(True))
            .order_by(RegimenFiscal.codigo)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ---------------------------------------------------------------
    # OBTENER POR ID
    # ---------------------------------------------------------------
    async def obtener_por_id(self, regimen_id: UUID) -> RegimenFiscal | None:
        query = select(RegimenFiscal).where(RegimenFiscal.id == regimen_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ---------------------------------------------------------------
    # OBTENER FORMULARIOS SAT ASOCIADOS
    # ---------------------------------------------------------------
    async def obtener_formularios_asociados(self, regimen_id: UUID) -> list[dict]:
        query = (
            select(FormularioSat)
            .join(RegimenFormularioSat)
            .where(RegimenFormularioSat.regimen_id == regimen_id)
            .where(FormularioSat.es_version_activa.is_(True))
            .order_by(FormularioSat.codigo)
        )
        result = await self.db.execute(query)
        formularios = result.scalars().all()

        # Enriquecer con bandera es_obligatorio desde la tabla puente
        puente_query = select(RegimenFormularioSat).where(
            RegimenFormularioSat.regimen_id == regimen_id
        )
        puente_result = await self.db.execute(puente_query)
        puente_map = {p.formulario_id: p.es_obligatorio for p in puente_result.scalars()}

        return [
            {
                "id": f.id,
                "codigo": f.codigo,
                "version": f.version,
                "nombre": f.nombre,
                "es_obligatorio": puente_map.get(f.id, True),
            }
            for f in formularios
        ]

    # ---------------------------------------------------------------
    # CREAR
    # ---------------------------------------------------------------
    async def crear(self, data: dict) -> RegimenFiscal:
        # Validar unicidad de código
        existente = await self.db.execute(
            select(RegimenFiscal).where(RegimenFiscal.codigo == data["codigo"])
        )
        if existente.scalar_one_or_none():
            raise ValueError(f"Ya existe un régimen con código '{data['codigo']}'")

        regimen = RegimenFiscal(**data)
        self.db.add(regimen)
        await self.db.commit()
        await self.db.refresh(regimen)
        return regimen

    # ---------------------------------------------------------------
    # ACTUALIZAR
    # ---------------------------------------------------------------
    async def actualizar(self, regimen_id: UUID, data: dict) -> RegimenFiscal | None:
        regimen = await self.obtener_por_id(regimen_id)
        if not regimen:
            return None

        # Si cambia el código, validar unicidad
        if "codigo" in data and data["codigo"] != regimen.codigo:
            existente = await self.db.execute(
                select(RegimenFiscal).where(RegimenFiscal.codigo == data["codigo"])
            )
            if existente.scalar_one_or_none():
                raise ValueError(f"Ya existe un régimen con código '{data['codigo']}'")

        for campo, valor in data.items():
            setattr(regimen, campo, valor)

        await self.db.commit()
        await self.db.refresh(regimen)
        return regimen

    # ---------------------------------------------------------------
    # ELIMINAR (soft delete)
    # ---------------------------------------------------------------
    async def eliminar(self, regimen_id: UUID) -> bool:
        regimen = await self.obtener_por_id(regimen_id)
        if not regimen:
            return False
        regimen.is_active = False
        await self.db.commit()
        return True