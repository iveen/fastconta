"""Service para Tipos de Libro SAT"""

from app.models.global_models import TipoLibro
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class TipoLibroService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def obtener_todos(
        self,
        is_active: bool | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[TipoLibro], int]:
        """Lista tipos de libro con filtros y paginación"""
        query = select(TipoLibro)

        if is_active is not None:
            query = query.where(TipoLibro.is_active == is_active)

        if search:
            search_term = f"%{search}%"
            query = query.where(
                (TipoLibro.codigo.ilike(search_term)) |
                (TipoLibro.nombre.ilike(search_term))
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.order_by(TipoLibro.codigo).offset(skip).limit(limit)
        result = await self.db.execute(query)
        tipos = result.scalars().all()

        return tipos, total

    async def obtener_todos_activos(self) -> list[TipoLibro]:
        """Lista todos los tipos de libro activos"""
        query = select(TipoLibro).where(
            TipoLibro.is_active.is_(True)
        ).order_by(TipoLibro.codigo)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def obtener_por_id(self, tipo_id: int) -> TipoLibro | None:
        """Obtiene un tipo de libro por ID"""
        query = select(TipoLibro).where(TipoLibro.id == tipo_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def crear(self, data: dict) -> TipoLibro:
        """Crea un nuevo tipo de libro"""
        # Verificar que el código no exista
        existing = await self.obtener_por_codigo(data.get("codigo"))
        if existing:
            raise ValueError(f"Ya existe un tipo de libro con código {data['codigo']}")

        tipo = TipoLibro(**data)
        self.db.add(tipo)
        await self.db.commit()
        await self.db.refresh(tipo)
        return tipo

    async def actualizar(self, tipo_id: int, data: dict) -> TipoLibro | None:
        """Actualiza un tipo de libro"""
        tipo = await self.obtener_por_id(tipo_id)
        if not tipo:
            return None

        # Verificar que el código no exista en otro registro
        if "codigo" in data and data["codigo"] != tipo.codigo:
            existing = await self.obtener_por_codigo(data["codigo"])
            if existing and existing.id != tipo_id:
                raise ValueError(f"Ya existe un tipo de libro con código {data['codigo']}")

        for key, value in data.items():
            setattr(tipo, key, value)

        await self.db.commit()
        await self.db.refresh(tipo)
        return tipo

    async def eliminar(self, tipo_id: int) -> bool:
        """Elimina un tipo de libro (soft delete)"""
        tipo = await self.obtener_por_id(tipo_id)
        if not tipo:
            return False

        tipo.is_active = False
        await self.db.commit()
        return True

    async def obtener_por_codigo(self, codigo: str) -> TipoLibro | None:
        """Obtiene un tipo de libro por código"""
        query = select(TipoLibro).where(TipoLibro.codigo == codigo)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()