from typing import List

from app.models.tenant_models import InventarioProducto
from app.schemas.inventario.producto import ProductoCreate, ProductoUpdate
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session


class ProductoService:
    """Servicio para gestión del catálogo de productos."""

    def __init__(self, db: Session):
        self.db = db

    def crear(
        self,
        tenant_id: int,
        empresa_id: int,
        data: ProductoCreate,
        usuario_id: int | None = None,
    ) -> InventarioProducto:
        # Convertir cuenta_inventario_public_id → cuenta_inventario_id
        data_dict = self._resolver_cuenta(data.model_dump())
        producto = InventarioProducto(
            tenant_id=tenant_id,
            empresa_id=empresa_id,
            created_by=usuario_id,
            updated_by=usuario_id,
            **data_dict,
        )
        self.db.add(producto)
        self.db.commit()
        self.db.refresh(producto)
        return producto

    def listar(
        self,
        tenant_id: int,
        empresa_id: int,
        search: str | None = None,
    ) -> List[InventarioProducto]:
        query = self.db.query(InventarioProducto).filter(
            and_(
                InventarioProducto.tenant_id == tenant_id,
                InventarioProducto.empresa_id == empresa_id,
                InventarioProducto.is_active.is_(True),
            )
        )
        if search:
            like = f"%{search}%"
            query = query.filter(
                or_(
                    InventarioProducto.codigo.ilike(like),
                    InventarioProducto.descripcion.ilike(like),
                )
            )
        return query.order_by(InventarioProducto.codigo).all()

    def obtener_por_codigo(
        self, tenant_id: int, empresa_id: int, codigo: str
    ) -> InventarioProducto | None:
        return (
            self.db.query(InventarioProducto)
            .filter(
                and_(
                    InventarioProducto.tenant_id == tenant_id,
                    InventarioProducto.empresa_id == empresa_id,
                    InventarioProducto.codigo == codigo,
                    InventarioProducto.is_active.is_(True),
                )
            )
            .first()
        )

    def actualizar(
        self,
        producto: InventarioProducto,
        data: ProductoUpdate,
        usuario_id: int | None = None,
    ) -> InventarioProducto:
        data_dict = self._resolver_cuenta(data.model_dump(exclude_unset=True))
        for key, value in data_dict.items():
            setattr(producto, key, value)
        producto.updated_by = usuario_id
        self.db.commit()
        self.db.refresh(producto)
        return producto

    def eliminar(
        self,
        producto: InventarioProducto,
        usuario_id: int | None = None,
    ) -> None:
        """Soft delete del producto."""
        from sqlalchemy.sql import func
        producto.is_active = False
        producto.deleted_at = func.now()
        producto.updated_by = usuario_id
        self.db.commit()

    def _resolver_cuenta(self, data_dict: dict) -> dict:
        """
        Convierte cuenta_inventario_public_id → cuenta_inventario_id.
        Si el dict no tiene public_id, lo retorna tal cual.
        """
        public_id = data_dict.pop("cuenta_inventario_public_id", None)
        if public_id:
            from app.models.tenant_models import CuentaContable
            cuenta = (
                self.db.query(CuentaContable)
                .filter_by(public_id=public_id)
                .first()
            )
            data_dict["cuenta_inventario_id"] = cuenta.id if cuenta else None
        return data_dict