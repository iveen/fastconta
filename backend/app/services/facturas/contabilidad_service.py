# app/services/facturas/contabilidad_service.py
"""
Servicio responsable de toda la lógica contable derivada de facturas:
- Clasificación de gastos según SAT
- Generación de partidas contables
- Mapeo de cuentas predeterminadas
- Validación de cuadratura
"""
import logging

from app.models.tenant_models import (
    CuentaContable,
    DetallePartida,
    FacturaElectronica,
    Partida,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ============================================================
# MAPEO DE CUENTAS PREDeterminadas POR TIPO DE OPERACIÓN
# ============================================================
CUENTAS_DEFAULT = {
    "IVA_POR_COBRAR": "1.1.4",      # Débito fiscal / IVA crédito
    "IVA_POR_PAGAR": "2.1.4",       # IVA débito (ventas)
    "COSTO_VENTAS": "5.1",
    "GASTO_GENERAL": "5.2",
    "GASTO_COMBUSTIBLE": "5.2.1",
    "GASTO_VEHICULO": "5.2.2",
    "PROVEEDORES": "2.1.1",
    "CLIENTES": "1.1.2",
    "ACTIVO_FIJO": "1.5",
    "VENTAS": "4.1",
}

# ============================================================
# CLASIFICACIÓN DE GASTOS SAT
# ============================================================
async def clasificar_gasto_sat(datos: dict) -> str:
    """
    Clasifica el gasto basado en las descripciones de los items.
    Retorna una de: NORMAL, COMBUSTIBLE, ACTIVO_FIJO, MEDICAMENTO, etc.
    """
    items = datos.get('items', [])
    descripcion_combinada = ' '.join(
        [str(item.get('descripcion', '')).lower() for item in items]
    )

    reglas = [
        (['gasolina', 'diesel', 'combustible'], 'COMBUSTIBLE'),
        (['medicamento', 'farmacia', 'medicina'], 'MEDICAMENTO'),
        (['vehiculo', 'vehículo', 'carro', 'automovil'], 'VEHICULO'),
        (['computadora', 'laptop', 'equipo computo'], 'ACTIVO_FIJO'),
        (['mobiliario', 'mueble', 'escritorio'], 'ACTIVO_FIJO'),
        (['maquinaria', 'maquina'], 'ACTIVO_FIJO'),
    ]

    for keywords, categoria in reglas:
        if any(kw in descripcion_combinada for kw in keywords):
            return categoria

    return 'NORMAL'


# ============================================================
# OBTENER CUENTAS PREDeterminadas
# ============================================================
async def obtener_cuentas_predeterminadas(
    db: AsyncSession,
    empresa_id: int,
    tipo_operacion: str = "Compra"
) -> dict:
    """
    Obtiene las cuentas contables predeterminadas según el tipo de operación.
    Retorna dict con las cuentas necesarias para generar la partida.
    """
    if tipo_operacion == "Compra":
        codigos_necesarios = [
            CUENTAS_DEFAULT["IVA_POR_COBRAR"],
            CUENTAS_DEFAULT["GASTO_GENERAL"],
            CUENTAS_DEFAULT["PROVEEDORES"],
        ]
    else:  # Venta
        codigos_necesarios = [
            CUENTAS_DEFAULT["CLIENTES"],
            CUENTAS_DEFAULT["VENTAS"],
            CUENTAS_DEFAULT["IVA_POR_PAGAR"],
        ]

    stmt = select(CuentaContable).where(
        CuentaContable.empresa_id == empresa_id,
        CuentaContable.codigo.in_(codigos_necesarios),
        CuentaContable.is_active.is_(True)
    )
    result = await db.execute(stmt)
    cuentas = {c.codigo: c for c in result.scalars().all()}

    # Validar que existan todas
    faltantes = [c for c in codigos_necesarios if c not in cuentas]
    if faltantes:
        raise ValueError(
            f"Faltan cuentas contables necesarias: {', '.join(faltantes)}. "
            f"Configure el plan de cuentas antes de generar partidas."
        )

    return cuentas


# ============================================================
# VALIDAR CUADRATURA DE PARTIDA
# ============================================================
def validar_partida_cuadrada(detalles: list[dict]) -> bool:
    """Valida que el debe sea igual al haber."""
    total_debe = sum(
        d["monto"] for d in detalles if d["tipo_movimiento"] == "debe"
    )
    total_haber = sum(
        d["monto"] for d in detalles if d["tipo_movimiento"] == "haber"
    )
    return total_debe == total_haber


# ============================================================
# GENERAR PARTIDA DESDE FACTURA (LÓGICA PRINCIPAL)
# ============================================================
async def generar_partida_desde_factura(
    db: AsyncSession,
    factura: FacturaElectronica,
    empresa_id: int,
    schema_name: str
) -> Partida:
    """
    Genera una partida contable a partir de una factura.
    
    Args:
        db: Sesión de BD
        factura: Objeto FacturaElectronica
        empresa_id: ID de la empresa (BIGINT)
        schema_name: Schema del tenant
    
    Returns:
        Partida creada con sus detalles
    
    Raises:
        ValueError: Si faltan cuentas o la partida no cuadra
    """
    # 1. Obtener cuentas predeterminadas
    cuentas = await obtener_cuentas_predeterminadas(
        db, empresa_id, factura.tipo_operacion
    )

    # 2. Construir detalles según tipo de operación
    detalles_partida = []

    if factura.tipo_operacion == "Compra":
        # Débitos: gasto + IVA
        if factura.total_gravado > 0:
            detalles_partida.append({
                "cuenta_id": cuentas[CUENTAS_DEFAULT["GASTO_GENERAL"]].id,
                "tipo_movimiento": "debe",
                "monto": factura.total_gravado
            })
        if factura.total_iva > 0:
            detalles_partida.append({
                "cuenta_id": cuentas[CUENTAS_DEFAULT["IVA_POR_COBRAR"]].id,
                "tipo_movimiento": "debe",
                "monto": factura.total_iva
            })
        # Crédito: proveedores
        detalles_partida.append({
            "cuenta_id": cuentas[CUENTAS_DEFAULT["PROVEEDORES"]].id,
            "tipo_movimiento": "haber",
            "monto": factura.total
        })
    else:  # Venta
        # Débito: clientes
        detalles_partida.append({
            "cuenta_id": cuentas[CUENTAS_DEFAULT["CLIENTES"]].id,
            "tipo_movimiento": "debe",
            "monto": factura.total
        })
        # Créditos: ventas + IVA
        if factura.total_gravado > 0:
            detalles_partida.append({
                "cuenta_id": cuentas[CUENTAS_DEFAULT["VENTAS"]].id,
                "tipo_movimiento": "haber",
                "monto": factura.total_gravado
            })
        if factura.total_iva > 0:
            detalles_partida.append({
                "cuenta_id": cuentas[CUENTAS_DEFAULT["IVA_POR_PAGAR"]].id,
                "tipo_movimiento": "haber",
                "monto": factura.total_iva
            })

    # 3. Validar cuadratura
    if not validar_partida_cuadrada(detalles_partida):
        total_debe = sum(d["monto"] for d in detalles_partida if d["tipo_movimiento"] == "debe")
        total_haber = sum(d["monto"] for d in detalles_partida if d["tipo_movimiento"] == "haber")
        raise ValueError(
            f"La partida no cuadra. Debe: {total_debe}, Haber: {total_haber}"
        )

    # 4. Crear la partida
    partida = Partida(
        fecha=factura.fecha_emision.date(),
        descripcion=f"Factura {factura.serie or ''} {factura.numero} - {factura.emisor_nombre}",
        numero_poliza=f"FEL-{factura.numero_autorizacion}",
        empresa_id=empresa_id,
        tipo_origen='factura_electronica'
    )
    db.add(partida)
    await db.flush()

    # 5. Crear los detalles
    for det in detalles_partida:
        db.add(DetallePartida(
            partida_id=partida.id,
            cuenta_id=det["cuenta_id"],
            tipo_movimiento=det["tipo_movimiento"],
            monto=det["monto"]
        ))

    await db.flush()
    await db.refresh(partida, ['detalles'])
    
    logger.info(
        f"✅ Partida generada desde factura {factura.numero_autorizacion}: "
        f"ID={partida.id}, Póliza={partida.numero_poliza}"
    )
    
    return partida


# ============================================================
# VALIDAR SI FACTURA YA TIENE PARTIDA ASOCIADA
# ============================================================
async def factura_tiene_partida(
    db: AsyncSession,
    factura_id: int,
    schema_name: str
) -> Partida | None:
    """Verifica si una factura ya tiene una partida generada."""
    stmt = select(Partida).where(
        Partida.numero_poliza.ilike("FEL-%"),
        Partida.descripcion.ilike(f"%{factura_id}%")
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()