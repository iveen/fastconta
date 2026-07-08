"""Servicio para gestión de Representantes Legales"""
from app.models.tenant_models import RepresentanteLegal
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession


class RepresentanteLegalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # QUERIES
    # ============================================================
    async def obtener_representantes_por_empresa(
        self, empresa_id: int, solo_activos: bool = True  # ✅ BIGINT
    ) -> list[RepresentanteLegal]:
        """Obtiene todos los representantes legales de una empresa"""
        query = select(RepresentanteLegal).where(
            RepresentanteLegal.empresa_id == empresa_id
        )
        if solo_activos:
            # ✅ CORREGIDO: is_active (del mixin SoftDelete) en lugar de es_activo
            query = query.where(RepresentanteLegal.is_active.is_(True))
        query = query.order_by(RepresentanteLegal.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def obtener_representante_por_id(
        self, representante_id: int, empresa_id: int  # ✅ BIGINT
    ) -> RepresentanteLegal | None:
        """Obtiene un representante legal específico"""
        query = select(RepresentanteLegal).where(
            and_(
                RepresentanteLegal.id == representante_id,
                RepresentanteLegal.empresa_id == empresa_id,
            )
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def verificar_duplicado(
        self,
        empresa_id: int,  # ✅ BIGINT
        tipo_identificacion: str,
        numero_identificacion: str,
        representante_id_excluir: int | None = None,  # ✅ BIGINT
    ) -> bool:
        """
        Verifica si ya existe un representante con el mismo tipo y número de identificación
        en la misma empresa.
        Returns True si existe (es duplicado), False si no existe.
        """
        query = select(func.count(RepresentanteLegal.id)).where(
            and_(
                RepresentanteLegal.empresa_id == empresa_id,
                RepresentanteLegal.tipo_identificacion == tipo_identificacion,
                RepresentanteLegal.numero_identificacion == numero_identificacion,
                # ✅ CORREGIDO: is_active en lugar de es_activo
                RepresentanteLegal.is_active.is_(True),
            )
        )
        if representante_id_excluir:
            query = query.where(RepresentanteLegal.id != representante_id_excluir)
        result = await self.db.execute(query)
        count = result.scalar()
        return count > 0

    # ============================================================
    # CRUD
    # ============================================================
    async def crear_representante(self, data: dict) -> RepresentanteLegal:
        """Crea un nuevo representante legal"""
        representante = RepresentanteLegal(**data)
        self.db.add(representante)
        await self.db.flush()
        await self.db.refresh(representante)
        return representante

    async def actualizar_representante(
        self, representante_id: int, empresa_id: int, data: dict  # ✅ BIGINT
    ) -> RepresentanteLegal | None:
        """Actualiza un representante legal existente"""
        representante = await self.obtener_representante_por_id(representante_id, empresa_id)
        if representante is None:
            return None
        for key, value in data.items():
            if hasattr(representante, key):
                setattr(representante, key, value)
        await self.db.flush()
        await self.db.refresh(representante)
        return representante

    async def eliminar_representante(
        self, representante_id: int, empresa_id: int  # ✅ BIGINT
    ) -> bool:
        """Elimina un representante legal (soft delete: is_active = False)"""
        representante = await self.obtener_representante_por_id(representante_id, empresa_id)
        if representante is None:
            return False
        # ✅ CORREGIDO: is_active en lugar de es_activo
        representante.is_active = False
        await self.db.flush()
        return True