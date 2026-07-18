from typing import List

from app.models.tenant_models import InventarioBodega
from app.schemas.inventario.bodega import BodegaCreate, BodegaUpdate
from sqlalchemy import and_
from sqlalchemy.orm import Session


class BodegaService:
    """Servicio para gestión del catálogo de bodegas."""

    def __init__(self, db: Session):
        self.db = db

    def crear(
        self,
        tenant_id: int,
        empresa_id: int,
        data: BodegaCreate,
        usuario_id: int | None = None,
    ) -> InventarioBodega:
        bodega = InventarioBodega(
            tenant_id=tenant_id,
            empresa_id=empresa_id,
            created_by=usuario_id,
            updated_by=usuario_id,
            **data.model_dump(),
        )
        self.db.add(bodega)
        self.db.commit()
        self.db.refresh(bodega)
        return bodega

    def listar(self, tenant_id: int, empresa_id: int) -> List[InventarioBodega]:
        return (
            self.db.query(InventarioBodega)
            .filter(
                and_(
                    InventarioBodega.tenant_id == tenant_id,
                    InventarioBodega.empresa_id == empresa_id,
                    InventarioBodega.is_active.is_(True),
                )
            )
            .order_by(InventarioBodega.codigo)
            .all()
        )

    def obtener_por_codigo(
        self, tenant_id: int, empresa_id: int, codigo: str
    ) -> InventarioBodega | None:
        return (
            self.db.query(InventarioBodega)
            .filter(
                and_(
                    InventarioBodega.tenant_id == tenant_id,
                    InventarioBodega.empresa_id == empresa_id,
                    InventarioBodega.codigo == codigo,
                    InventarioBodega.is_active.is_(True),
                )
            )
            .first()
        )

    def actualizar(
        self,
        bodega: InventarioBodega,
        data: BodegaUpdate,
        usuario_id: int | None = None,
    ) -> InventarioBodega:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(bodega, key, value)
        bodega.updated_by = usuario_id
        self.db.commit()
        self.db.refresh(bodega)
        return bodega

    def eliminar(
        self,
        bodega: InventarioBodega,
        usuario_id: int | None = None,
    ) -> None:
        """Soft delete de la bodega."""
        from sqlalchemy.sql import func
        bodega.is_active = False
        bodega.deleted_at = func.now()
        bodega.updated_by = usuario_id
        self.db.commit()

    def tiene_items_asociados(self, bodega_id: int) -> bool:
        """Verifica si la bodega tiene items de inventario asociados."""
        from app.models.tenant_models import InventarioItem
        return (
            self.db.query(InventarioItem)
            .filter_by(bodega_id=bodega_id)
            .first()
        ) is not None