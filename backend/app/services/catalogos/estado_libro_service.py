"""Service para Estados de Libro SAT"""

from app.models.global_models import EstadoLibro
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class EstadoLibroService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def obtener_todos(
        self,
        is_active: bool | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[EstadoLibro], int]:
        """Lista estados de libro con filtros y paginación"""
        query = select(EstadoLibro)

        if is_active is not None:
            query = query.where(EstadoLibro.is_active == is_active)

        if search:
            search_term = f"%{search}%"
            query = query.where(EstadoLibro.nombre.ilike(search_term))

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.order_by(EstadoLibro.nombre).offset(skip).limit(limit)
        result = await self.db.execute(query)
        estados = result.scalars().all()

        return estados, total

    async def obtener_todos_activos(self) -> list[EstadoLibro]:
        """Lista todos los estados de libro activos"""
        query = select(EstadoLibro).where(
            EstadoLibro.is_active.is_(True)
        ).order_by(EstadoLibro.nombre)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def obtener_por_id(self, estado_id: int) -> EstadoLibro | None:
        """Obtiene un estado de libro por ID"""
        query = select(EstadoLibro).where(EstadoLibro.id == estado_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def crear(self, data: dict) -> EstadoLibro:
        """Crea un nuevo estado de libro"""
        # Verificar que el nombre no exista
        existing = await self.obtener_por_nombre(data.get("nombre"))
        if existing:
            raise ValueError(f"Ya existe un estado de libro con nombre '{data['nombre']}'")

        estado = EstadoLibro(**data)
        self.db.add(estado)
        await self.db.commit()
        await self.db.refresh(estado)
        return estado

    async def actualizar(self, estado_id: int, data: dict) -> EstadoLibro | None:
        """Actualiza un estado de libro"""
        estado = await self.obtener_por_id(estado_id)
        if not estado:
            return None

        # Verificar que el nombre no exista en otro registro
        if "nombre" in data and data["nombre"] != estado.nombre:
            existing = await self.obtener_por_nombre(data["nombre"])
            if existing and existing.id != estado_id:
                raise ValueError(f"Ya existe un estado de libro con nombre '{data['nombre']}'")

        for key, value in data.items():
            setattr(estado, key, value)

        await self.db.commit()
        await self.db.refresh(estado)
        return estado

    async def eliminar(self, estado_id: int) -> bool:
        """Elimina un estado de libro (soft delete)"""
        estado = await self.obtener_por_id(estado_id)
        if not estado:
            return False

        estado.is_active = False
        await self.db.commit()
        return True

    async def obtener_por_nombre(self, nombre: str) -> EstadoLibro | None:
        """Obtiene un estado de libro por nombre"""
        query = select(EstadoLibro).where(EstadoLibro.nombre == nombre)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()