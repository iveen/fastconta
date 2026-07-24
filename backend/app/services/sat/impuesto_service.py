"""Service para Catálogo de Impuestos"""

from app.models.global_models import CatalogoImpuesto
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class ImpuestoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def obtener_todos(
        self,
        activo: bool | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[CatalogoImpuesto], int]:
        """Lista impuestos con filtros y paginación"""
        query = select(CatalogoImpuesto)

        if activo is not None:
            query = query.where(CatalogoImpuesto.is_active == activo)

        if search:
            search_term = f"%{search}%"
            query = query.where(
                (CatalogoImpuesto.codigo.ilike(search_term)) |
                (CatalogoImpuesto.nombre.ilike(search_term))
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.order_by(CatalogoImpuesto.codigo).offset(skip).limit(limit)
        result = await self.db.execute(query)
        impuestos = result.scalars().all()

        return impuestos, total

    async def obtener_todos_activos(self) -> list[CatalogoImpuesto]:
        """Lista todos los impuestos activos"""
        query = select(CatalogoImpuesto).where(
            CatalogoImpuesto.is_active.is_(True) 
        ).order_by(CatalogoImpuesto.codigo)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def obtener_por_id(self, impuesto_id: int) -> CatalogoImpuesto | None:
        """Obtiene un impuesto por ID"""
        query = select(CatalogoImpuesto).where(CatalogoImpuesto.id == impuesto_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def crear(self, data: dict) -> CatalogoImpuesto:
        """Crea un nuevo impuesto"""
        # Verificar que el código no exista
        existing = await self.obtener_por_codigo(data.get("codigo"))
        if existing:
            raise ValueError(f"Ya existe un impuesto con código {data['codigo']}")

        impuesto = CatalogoImpuesto(**data)
        self.db.add(impuesto)
        await self.db.commit()
        await self.db.refresh(impuesto)
        return impuesto

    async def actualizar(self, impuesto_id: int, data: dict) -> CatalogoImpuesto | None:
        """Actualiza un impuesto"""
        impuesto = await self.obtener_por_id(impuesto_id)
        if not impuesto:
            return None

        # Verificar que el código no exista en otro registro
        if "codigo" in data and data["codigo"] != impuesto.codigo:
            existing = await self.obtener_por_codigo(data["codigo"])
            if existing and existing.id != impuesto_id:
                raise ValueError(f"Ya existe un impuesto con código {data['codigo']}")

        for key, value in data.items():
            setattr(impuesto, key, value)

        await self.db.commit()
        await self.db.refresh(impuesto)
        return impuesto

    async def eliminar(self, impuesto_id: int) -> bool:
        """Elimina un impuesto (soft delete)"""
        impuesto = await self.obtener_por_id(impuesto_id)
        if not impuesto:
            return False

        impuesto.is_active = False
        await self.db.commit()
        return True

    async def obtener_por_codigo(self, codigo: str) -> CatalogoImpuesto | None:
        """Obtiene un impuesto por código"""
        query = select(CatalogoImpuesto).where(CatalogoImpuesto.codigo == codigo)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()