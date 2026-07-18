from typing import List
from uuid import UUID

from app.models.tenant_models import InventarioItem, InventarioToma
from app.schemas.inventario.toma import TomaCreate, TomaUpdate
from sqlalchemy import and_
from sqlalchemy.orm import Session, joinedload


class TomaService:
    """
    Servicio para gestión de tomas de inventario (cabecera).

    Responsabilidades:
    - CRUD de tomas (crear, listar, obtener, actualizar, eliminar)
    - Cambio de estado (confirmar)

    NO gestiona items → eso lo hace ItemService.
    """

    def __init__(self, db: Session):
        self.db = db

    def crear(
        self,
        tenant_id: int,
        data: TomaCreate,
        usuario_id: int | None = None,
    ) -> InventarioToma:
        """
        Crea una nueva toma de inventario.
        Valida unicidad por tenant + empresa + período fiscal.
        """
        existente = (
            self.db.query(InventarioToma)
            .filter(
                and_(
                    InventarioToma.tenant_id == tenant_id,
                    InventarioToma.empresa_id == data.empresa_id,
                    InventarioToma.anio_periodo == data.anio_periodo,
                    InventarioToma.mes_periodo == data.mes_periodo,
                )
            )
            .first()
        )
        if existente:
            raise ValueError(
                f"Ya existe una toma para esta empresa en el período "
                f"{data.anio_periodo}/{str(data.mes_periodo).zfill(2)}"
            )

        toma = InventarioToma(
            tenant_id=tenant_id,
            created_by=usuario_id,
            updated_by=usuario_id,
            **data.model_dump(),
        )
        self.db.add(toma)
        self.db.commit()
        self.db.refresh(toma)
        return toma

    def listar(
        self,
        tenant_id: int,
        empresa_id: int | None = None,
        estado: str | None = None,
        tipo: str | None = None,
        anio: int | None = None,
        mes: int | None = None,
    ) -> List[InventarioToma]:
        """Lista tomas con filtros opcionales, ordenadas por período descendente."""
        query = self.db.query(InventarioToma).filter(
            InventarioToma.tenant_id == tenant_id
        )
        if empresa_id:
            query = query.filter(InventarioToma.empresa_id == empresa_id)
        if estado:
            query = query.filter(InventarioToma.estado == estado)
        if tipo:
            query = query.filter(InventarioToma.tipo == tipo)
        if anio:
            query = query.filter(InventarioToma.anio_periodo == anio)
        if mes:
            query = query.filter(InventarioToma.mes_periodo == mes)

        return (
            query
            .order_by(
                InventarioToma.anio_periodo.desc(),
                InventarioToma.mes_periodo.desc(),
            )
            .all()
        )

    def obtener_con_items(
        self,
        public_id: UUID,
        tenant_id: int,
    ) -> InventarioToma | None:
        """Obtiene una toma con todos sus items cargados (eager loading)."""
        return (
            self.db.query(InventarioToma)
            .options(
                joinedload(InventarioToma.items)
                    .joinedload(InventarioItem.bodega),
                joinedload(InventarioToma.items)
                    .joinedload(InventarioItem.producto),
                joinedload(InventarioToma.empresa),
            )
            .filter(
                and_(
                    InventarioToma.public_id == public_id,
                    InventarioToma.tenant_id == tenant_id,
                )
            )
            .first()
        )

    def actualizar(
        self,
        toma: InventarioToma,
        data: TomaUpdate,
        usuario_id: int | None = None,
    ) -> InventarioToma:
        """Actualiza datos de la toma. No permite modificar si está CONTABILIZADO."""
        if toma.estado == "CONTABILIZADO":
            raise ValueError("No se puede modificar una toma ya contabilizada")

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(toma, key, value)
        toma.updated_by = usuario_id
        self.db.commit()
        self.db.refresh(toma)
        return toma

    def eliminar(self, toma: InventarioToma) -> None:
        """Elimina la toma y todos sus items (CASCADE). Solo si está en BORRADOR."""
        if toma.estado != "BORRADOR":
            raise ValueError("Solo se pueden eliminar tomas en estado BORRADOR")
        self.db.delete(toma)
        self.db.commit()

    def confirmar(
        self,
        toma: InventarioToma,
        usuario_id: int | None = None,
    ) -> InventarioToma:
        """
        Confirma una toma (cambia estado a CONFIRMADO).
        Requiere: estado BORRADOR + al menos un item.
        """
        if toma.estado != "BORRADOR":
            raise ValueError("Solo se pueden confirmar tomas en estado BORRADOR")

        if not toma.items:
            raise ValueError("No se puede confirmar una toma sin items")

        toma.estado = "CONFIRMADO"
        toma.updated_by = usuario_id
        self.db.commit()
        self.db.refresh(toma)
        return toma