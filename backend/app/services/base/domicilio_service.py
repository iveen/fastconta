"""Servicio para gestión de Domicilios"""
from app.models.tenant_models import Domicilio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class DomicilioService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # QUERIES
    # ============================================================
    async def obtener_domicilios_por_empresa(
        self, empresa_id: int  # ✅ BIGINT (era UUID)
    ) -> list[Domicilio]:
        """Obtiene todos los domicilios de una empresa con relaciones"""
        query = (
            select(Domicilio)
            .options(
                selectinload(Domicilio.tipo_domicilio),
                selectinload(Domicilio.departamento),
                selectinload(Domicilio.municipio),
            )
            .where(Domicilio.empresa_id == empresa_id)
            .order_by(Domicilio.tipo_domicilio_id)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def obtener_domicilio_por_id(
        self, domicilio_id: int, empresa_id: int  # ✅ BIGINT (era UUID)
    ) -> Domicilio | None:
        """Obtiene un domicilio específico con relaciones"""
        query = (
            select(Domicilio)
            .options(
                selectinload(Domicilio.tipo_domicilio),
                selectinload(Domicilio.departamento),
                selectinload(Domicilio.municipio),
            )
            .where(
                Domicilio.id == domicilio_id,
                Domicilio.empresa_id == empresa_id,
            )
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    # ============================================================
    # CRUD
    # ============================================================
    async def crear_domicilio(self, data: dict) -> Domicilio:
        """Crea un nuevo domicilio"""
        domicilio = Domicilio(**data)
        self.db.add(domicilio)
        await self.db.flush()
        await self.db.refresh(domicilio)
        # Recargar con relaciones
        return await self.obtener_domicilio_por_id(
            domicilio.id, domicilio.empresa_id
        )

    async def actualizar_domicilio(
        self, domicilio_id: int, empresa_id: int, data: dict  # ✅ BIGINT
    ) -> Domicilio | None:
        """Actualiza un domicilio existente"""
        domicilio = await self.obtener_domicilio_por_id(domicilio_id, empresa_id)
        if domicilio is None:
            return None
        for key, value in data.items():
            if hasattr(domicilio, key):
                setattr(domicilio, key, value)
        await self.db.flush()
        await self.db.refresh(domicilio)
        # Recargar con relaciones
        return await self.obtener_domicilio_por_id(domicilio_id, empresa_id)

    async def eliminar_domicilio(
        self, domicilio_id: int, empresa_id: int  # ✅ BIGINT
    ) -> bool:
        """Elimina un domicilio (hard delete)"""
        domicilio = await self.obtener_domicilio_por_id(domicilio_id, empresa_id)
        if domicilio is None:
            return False
        await self.db.delete(domicilio)
        await self.db.flush()
        return True

    # ============================================================
    # HELPERS
    # ============================================================
    @staticmethod
    def enriquecer_domicilio(domicilio: Domicilio) -> dict:
        """Convierte un Domicilio ORM a dict con nombres de relaciones resueltos"""
        return {
            "id": domicilio.id,
            "empresa_id": domicilio.empresa_id,
            "tipo_domicilio_id": domicilio.tipo_domicilio_id,
            "departamento_id": domicilio.departamento_id,
            "municipio_id": domicilio.municipio_id,
            "direccion_exacta": domicilio.direccion_exacta,
            "zona": domicilio.zona,
            "codigo_postal": domicilio.codigo_postal,
            "tipo_domicilio_nombre": domicilio.tipo_domicilio.nombre if domicilio.tipo_domicilio else None,
            "departamento_nombre": domicilio.departamento.nombre if domicilio.departamento else None,
            "municipio_nombre": domicilio.municipio.nombre if domicilio.municipio else None,
        }