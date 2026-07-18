"""
Helpers compartidos para convertir modelos ORM → schemas de respuesta.
Centraliza la lógica de mapeo public_id ↔ id.
"""
from uuid import UUID

from app.models.tenant_models import (
    InventarioBodega,
    InventarioImportacion,
    InventarioItem,
    InventarioProducto,
    InventarioToma,
)
from app.schemas.inventario.bodega import BodegaResponse
from app.schemas.inventario.costo_ventas import CostoVentasResponse
from app.schemas.inventario.importacion import ImportacionResponse
from app.schemas.inventario.item import ItemResponse
from app.schemas.inventario.producto import ProductoResponse
from app.schemas.inventario.toma import (
    ItemResumen,
    TomaListResponse,
    TomaResponse,
)


def bodega_a_response(b: InventarioBodega) -> BodegaResponse:
    return BodegaResponse(
        public_id=b.public_id,
        empresa_id=b.empresa.public_id if b.empresa else UUID(int=0),
        codigo=b.codigo,
        nombre=b.nombre,
        ubicacion=b.ubicacion,
        is_active=b.is_active,
        deleted_at=b.deleted_at,
        created_at=b.created_at,
    )


def producto_a_response(p: InventarioProducto) -> ProductoResponse:
    return ProductoResponse(
        public_id=p.public_id,
        empresa_id=p.empresa.public_id if p.empresa else UUID(int=0),
        codigo=p.codigo,
        descripcion=p.descripcion,
        unidad_medida=p.unidad_medida,
        cuenta_inventario_public_id=(
            p.cuenta_inventario.public_id if p.cuenta_inventario else None
        ),
        is_active=p.is_active,
        created_at=p.created_at,
    )


def item_a_response(i: InventarioItem) -> ItemResponse:
    return ItemResponse(
        public_id=i.public_id,
        toma_public_id=i.toma.public_id if i.toma else UUID(int=0),
        producto_public_id=i.producto.public_id if i.producto else None,
        bodega_public_id=i.bodega.public_id if i.bodega else None,
        codigo=i.codigo,
        descripcion=i.descripcion,
        unidad_medida=i.unidad_medida,
        cantidad=i.cantidad,
        costo_unitario=i.costo_unitario,
        costo_total=i.costo_total,
        bodega_codigo=i.bodega_codigo,
    )


def item_a_resumen(i: InventarioItem) -> ItemResumen:
    return ItemResumen(
        public_id=i.public_id,
        codigo=i.codigo,
        descripcion=i.descripcion,
        cantidad=i.cantidad,
        costo_unitario=i.costo_unitario,
        costo_total=i.costo_total,
        bodega_codigo=i.bodega_codigo,
        unidad_medida=i.unidad_medida,
    )


def toma_a_response(t: InventarioToma) -> TomaResponse:
    return TomaResponse(
        public_id=t.public_id,
        empresa_public_id=t.empresa.public_id if t.empresa else UUID(int=0),
        anio_periodo=t.anio_periodo,
        mes_periodo=t.mes_periodo,
        fecha_corte=t.fecha_corte,
        tipo=t.tipo,
        metodo_valuacion=t.metodo_valuacion,
        estado=t.estado,
        observaciones=t.observaciones,
        partida_ajuste_public_id=(
            t.partida_ajuste.public_id if t.partida_ajuste else None
        ),
        total_items=t.total_items,
        valor_total=t.valor_total,
        created_at=t.created_at,
        updated_at=t.updated_at,
        items=[item_a_resumen(i) for i in t.items] if t.items else [],
    )


def toma_a_list_response(t: InventarioToma) -> TomaListResponse:
    return TomaListResponse(
        public_id=t.public_id,
        empresa_public_id=t.empresa.public_id if t.empresa else UUID(int=0),
        anio_periodo=t.anio_periodo,
        mes_periodo=t.mes_periodo,
        fecha_corte=t.fecha_corte,
        tipo=t.tipo,
        metodo_valuacion=t.metodo_valuacion,
        estado=t.estado,
        total_items=t.total_items,
        valor_total=t.valor_total,
        created_at=t.created_at,
    )


def importacion_a_response(i: InventarioImportacion) -> ImportacionResponse:
    return ImportacionResponse(
        public_id=i.public_id,
        toma_public_id=i.toma.public_id if i.toma else UUID(int=0),
        archivo_original=i.archivo_original,
        formato=i.formato,
        modo=i.modo,
        filas_procesadas=i.filas_procesadas,
        filas_validas=i.filas_validas,
        filas_con_error=i.filas_con_error,
        errores=i.errores,
        created_at=i.created_at,
    )


def costo_ventas_a_response(data: dict) -> CostoVentasResponse:
    return CostoVentasResponse(
        toma_public_id=str(data["toma_public_id"]),
        empresa_public_id=str(data["empresa_public_id"]),
        periodo_actual=data["periodo_actual"],
        periodo_desde=data["periodo_desde"],
        periodo_hasta=data["periodo_hasta"],
        inventario_inicial=data["inventario_inicial"],
        compras_periodo=data["compras_periodo"],
        inventario_final=data["inventario_final"],
        costo_ventas=data["costo_ventas"],
    )