from decimal import Decimal

from app.models.tenant_models import (
    InventarioBodega,
    InventarioItem,
    InventarioProducto,
    InventarioToma,
)
from app.schemas.inventario.item import ItemCreate, ItemUpdate
from sqlalchemy import and_, func
from sqlalchemy.orm import Session


class ItemService:
    """
    Servicio para gestión de items dentro de una toma de inventario.

    Responsabilidades:
    - Agregar/actualizar/eliminar items
    - Resolver producto/bodega por public_id o código
    - Recalcular totales de la toma (total_items, valor_total)
    """

    def __init__(self, db: Session):
        self.db = db

    def agregar(
        self,
        toma: InventarioToma,
        data: ItemCreate,
        usuario_id: int | None = None,
    ) -> InventarioItem:
        """
        Agrega un item a una toma.
        Solo permitido si la toma está en estado BORRADOR.
        """
        if toma.estado != "BORRADOR":
            raise ValueError("Solo se pueden agregar items en tomas BORRADOR")

        producto_id = self._resolver_producto(
            toma.tenant_id, toma.empresa_id,
            data.producto_public_id, data.codigo
        )
        bodega_id = self._resolver_bodega(
            toma.tenant_id, toma.empresa_id,
            data.bodega_public_id, data.bodega_codigo
        )

        costo_total = (data.cantidad * data.costo_unitario).quantize(
            Decimal("0.01")
        )
        item_data = data.model_dump(
            exclude={"producto_public_id", "bodega_public_id"}
        )

        item = InventarioItem(
            toma_id=toma.id,
            producto_id=producto_id,
            bodega_id=bodega_id,
            costo_total=costo_total,
            created_by=usuario_id,
            updated_by=usuario_id,
            **item_data,
        )
        self.db.add(item)
        self.db.flush()
        self.recalcular_totales(toma)
        self.db.commit()
        self.db.refresh(item)
        return item

    def actualizar(
        self,
        item: InventarioItem,
        data: ItemUpdate,
        usuario_id: int | None = None,
    ) -> InventarioItem:
        """
        Actualiza un item. Recalcula costo_total y totales de la toma.
        Solo permitido si la toma está en estado BORRADOR.
        """
        if item.toma.estado != "BORRADOR":
            raise ValueError("Solo se pueden modificar items en tomas BORRADOR")

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(item, key, value)

        item.costo_total = (item.cantidad * item.costo_unitario).quantize(
            Decimal("0.01")
        )
        item.updated_by = usuario_id
        self.recalcular_totales(item.toma)
        self.db.commit()
        self.db.refresh(item)
        return item

    def eliminar(self, item: InventarioItem) -> None:
        """
        Elimina un item y recalcula totales de la toma.
        Solo permitido si la toma está en estado BORRADOR.
        """
        if item.toma.estado != "BORRADOR":
            raise ValueError("Solo se pueden eliminar items en tomas BORRADOR")

        toma = item.toma
        self.db.delete(item)
        self.db.flush()
        self.recalcular_totales(toma)
        self.db.commit()

    def recalcular_totales(self, toma: InventarioToma) -> None:
        """
        Recalcula total_items y valor_total de una toma.
        Método público para que ImportService también pueda usarlo.
        """
        resultado = (
            self.db.query(
                func.count(InventarioItem.id),
                func.coalesce(func.sum(InventarioItem.costo_total), 0),
            )
            .filter(InventarioItem.toma_id == toma.id)
            .first()
        )
        toma.total_items = resultado[0] or 0
        toma.valor_total = resultado[1] or Decimal("0.00")

    # ============================================================
    # MÉTODOS PRIVADOS DE RESOLUCIÓN
    # ============================================================

    def _resolver_producto(
        self,
        tenant_id: int,
        empresa_id: int,
        public_id: str | None,
        codigo: str | None,
    ) -> int | None:
        """Resuelve producto por public_id (prioridad) o por código."""
        if public_id:
            prod = (
                self.db.query(InventarioProducto)
                .filter(
                    and_(
                        InventarioProducto.public_id == public_id,
                        InventarioProducto.tenant_id == tenant_id,
                        InventarioProducto.empresa_id == empresa_id,
                    )
                )
                .first()
            )
            if prod:
                return prod.id

        if codigo:
            prod = (
                self.db.query(InventarioProducto)
                .filter(
                    and_(
                        InventarioProducto.tenant_id == tenant_id,
                        InventarioProducto.empresa_id == empresa_id,
                        InventarioProducto.codigo == codigo,
                    )
                )
                .first()
            )
            if prod:
                return prod.id

        return None

    def _resolver_bodega(
        self,
        tenant_id: int,
        empresa_id: int,
        public_id: str | None,
        codigo: str | None,
    ) -> int | None:
        """Resuelve bodega por public_id (prioridad) o por código."""
        if public_id:
            bod = (
                self.db.query(InventarioBodega)
                .filter(
                    and_(
                        InventarioBodega.public_id == public_id,
                        InventarioBodega.tenant_id == tenant_id,
                        InventarioBodega.empresa_id == empresa_id,
                    )
                )
                .first()
            )
            if bod:
                return bod.id

        if codigo:
            bod = (
                self.db.query(InventarioBodega)
                .filter(
                    and_(
                        InventarioBodega.tenant_id == tenant_id,
                        InventarioBodega.empresa_id == empresa_id,
                        InventarioBodega.codigo == codigo,
                    )
                )
                .first()
            )
            if bod:
                return bod.id

        return None