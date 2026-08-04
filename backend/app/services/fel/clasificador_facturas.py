"""
Clasificador de Facturas Electrónicas

Calcula campos denormalizados para optimizar las reglas de filtrado del motor
de declaraciones SAT. Estos campos se calculan al momento de la ingestión FEL
y se almacenan en FacturaElectronica para evitar joins costosos.

Estrategia de clasificación (en orden de prioridad):
  1. Impuestos especiales registrados (FacturaImpuestoEspecial) → más preciso
  2. Heurística por descripción de items → fallback cuando no hay impuestos
  3. Tipo de documento (CEXE, FYDUCA, etc.)
  4. Régimen fiscal del emisor (pequeño contribuyente)
  5. País de destino (región Centroamérica vs resto)
  6. Detalles de factura (bien/servicio predominante)
"""

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import ClasificacionGastoSAT
from app.models.global_models import RegimenFiscal
from app.models.tenant_models import (
    Empresa,
    FacturaDetalle,
    FacturaElectronica,
    FacturaImpuestoEspecial,
)

logger = logging.getLogger(__name__)

# ============================================================
# CONSTANTES
# ============================================================
PAISES_CENTROAMERICA = {
    "GUATEMALA",
    "BELICE",
    "EL SALVADOR",
    "HONDURAS",
    "NICARAGUA",
    "COSTA RICA",
    "PANAMA",
    "PANAMÁ",  # Con tilde por si viene así
}

# Códigos de impuestos especiales del catálogo global
CODIGOS_MEDICAMENTO = {
    "MEDICAMENTO",
    "MEDICAMENTO_GENERICO",
    "ANTIRRETROVIRAL",
    "MEDICAMENTO_ALTERNATIVO",
}

CODIGOS_VEHICULO = {
    "VEHICULO",
    "VEHICULO_TERRESTRE",
    "VEHICULO_USADO",
    "VEHICULO_NUEVO",
}

# Códigos de régimen fiscal para pequeños contribuyentes
CODIGOS_PEQUENO_CONTRIBUYENTE = {
    "PC_FEL",
    "PEQUENO_CONTRIBUYENTE",
    "PC",
}

# ============================================================
# HEURÍSTICA POR DESCRIPCIÓN (fallback cuando no hay impuestos especiales)
# ============================================================
# Keywords para detectar medicamentos por descripción de items
KEYWORDS_MEDICAMENTO = [
    "medicamento", "farmacia", "medicina", "antirretroviral",
    "paracetamol", "ibuprofeno", "amoxicilina", "omeprazol",
    "genérico", "generico",
]

# Keywords para detectar vehículos por descripción de items
KEYWORDS_VEHICULO = [
    "vehiculo", "vehículo", "carro", "automovil", "automóvil",
    "motocicleta", "moto", "camioneta", "pickup", "tracto",
    "trailer", "remolque",
]

# Keywords para detectar combustible
KEYWORDS_COMBUSTIBLE = [
    "gasolina", "diesel", "diésel", "combustible",
    "super", "regular", "premium", "biodiesel",
]

# Keywords para detectar activo fijo
KEYWORDS_ACTIVO_FIJO = [
    "computadora", "laptop", "equipo computo", "equipo cómputo",
    "mobiliario", "mueble", "escritorio", "silla de oficina",
    "maquinaria", "maquina", "máquina", "herramienta industrial",
    "impresora", "servidor", "monitor",
]


# ============================================================
# FUNCIONES DE CLASIFICACIÓN
# ============================================================
def clasificar_region_destino(
    pais_destino: str | None,
    es_exportacion: bool,
    es_importacion: bool,
) -> str | None:
    """
    Clasifica la región de destino de la factura.

    Returns:
        "LOCAL" | "CENTROAMERICA" | "RESTO_MUNDO" | None
    """
    if not es_exportacion and not es_importacion:
        return "LOCAL"

    if not pais_destino:
        return None

    pais_upper = pais_destino.upper().strip()

    if pais_upper in PAISES_CENTROAMERICA:
        return "CENTROAMERICA"

    return "RESTO_MUNDO"


def clasificar_bien_o_servicio_predominante(detalles: list) -> str | None:
    """
    Determina si la factura es predominantemente de bienes, servicios o mixta.

    Returns:
        "B" | "S" | "M" | None
    """
    if not detalles:
        return None

    bienes = sum(1 for d in detalles if getattr(d, "bien_o_servicio", "") == "B")
    servicios = sum(1 for d in detalles if getattr(d, "bien_o_servicio", "") == "S")

    if bienes > 0 and servicios == 0:
        return "B"
    elif servicios > 0 and bienes == 0:
        return "S"
    elif bienes > 0 and servicios > 0:
        return "M"

    return None


def clasificar_por_impuestos_especiales(
    impuestos_especiales: list[FacturaImpuestoEspecial],
) -> dict[str, bool]:
    """
    Clasifica la factura según los impuestos especiales asociados.

    Returns:
        Dict con booleanos: es_medicamento, es_vehiculo
    """
    if not impuestos_especiales:
        return {
            "es_medicamento": False,
            "es_vehiculo": False,
        }

    # Obtener códigos de los catálogos
    codigos = set()
    for imp in impuestos_especiales:
        if imp.catalogo and imp.catalogo.codigo:
            codigos.add(imp.catalogo.codigo.upper())

    return {
        "es_medicamento": bool(codigos & CODIGOS_MEDICAMENTO),
        "es_vehiculo": bool(codigos & CODIGOS_VEHICULO),
    }


def clasificar_por_heuristica_descripcion(detalles: list[FacturaDetalle]) -> dict[str, bool]:
    """
    Clasifica la factura por heurística basada en descripciones de items.

    Este es el FALLBACK cuando no hay impuestos especiales registrados.
    Usa las mismas keywords que clasificar_gasto_sat() en contabilidad_service.py
    para mantener consistencia.

    Returns:
        Dict con booleanos: es_medicamento, es_vehiculo, es_combustible, es_activo_fijo
    """
    resultado = {
        "es_medicamento": False,
        "es_vehiculo": False,
        "es_combustible": False,
        "es_activo_fijo": False,
    }

    if not detalles:
        return resultado

    # Concatenar todas las descripciones en minúsculas
    descripcion_combinada = " ".join(
        (d.descripcion or "").lower() for d in detalles if d.descripcion
    )

    if not descripcion_combinada.strip():
        return resultado

    # Detectar por keywords
    if any(kw in descripcion_combinada for kw in KEYWORDS_MEDICAMENTO):
        resultado["es_medicamento"] = True
    if any(kw in descripcion_combinada for kw in KEYWORDS_VEHICULO):
        resultado["es_vehiculo"] = True
    if any(kw in descripcion_combinada for kw in KEYWORDS_COMBUSTIBLE):
        resultado["es_combustible"] = True
    if any(kw in descripcion_combinada for kw in KEYWORDS_ACTIVO_FIJO):
        resultado["es_activo_fijo"] = True

    return resultado


def clasificar_tipo_documento(tipo_documento: str | None) -> dict[str, bool]:
    """
    Clasifica según el tipo de documento.

    Returns:
        Dict con booleanos: tiene_constancia_exencion, es_no_afecta
    """
    if not tipo_documento:
        return {
            "tiene_constancia_exencion": False,
            "es_no_afecta": False,
        }

    tipo_upper = tipo_documento.upper().strip()

    return {
        "tiene_constancia_exencion": tipo_upper == "CEXE",
        "es_no_afecta": tipo_upper in ("NO_AFECTA", "DEC29-89"),
    }


async def clasificar_pequeno_contribuyente(
    db: AsyncSession,
    emisor_nit: str,
    empresa_id: int,
) -> bool:
    """
    Determina si el emisor es pequeño contribuyente.

    Optimizado: un solo query con JOIN en lugar de dos queries secuenciales.
    """
    if not emisor_nit:
        return False

    # Query optimizado: JOIN directo para obtener el código del régimen
    stmt = (
        select(RegimenFiscal.codigo)
        .join(Empresa, Empresa.regimen_fiscal_id == RegimenFiscal.id)
        .where(
            Empresa.nit == emisor_nit.replace("-", "").strip(),
            Empresa.tenant_id == empresa_id,
            RegimenFiscal.is_active.is_(True),
            Empresa.is_active.is_(True),
        )
        .limit(1)
    )
    result = await db.execute(stmt)
    codigo_regimen = result.scalar_one_or_none()

    if not codigo_regimen:
        return False

    return codigo_regimen.upper() in CODIGOS_PEQUENO_CONTRIBUYENTE


def derivar_clasificacion_gasto_sat(
    clasificacion: dict[str, bool],
) -> str:
    """
    Deriva el valor de clasificacion_gasto_sat (string) a partir de los
    booleanos calculados, usando el enum ClasificacionGastoSAT.

    Orden de prioridad (el primero que sea True gana):
      1. COMBUSTIBLE
      2. MEDICAMENTO
      3. VEHICULO
      4. ACTIVO_FIJO
      5. NORMAL (default)

    Returns:
        String del enum ClasificacionGastoSAT
    """
    if clasificacion.get("es_combustible"):
        return ClasificacionGastoSAT.COMBUSTIBLE.value
    if clasificacion.get("es_medicamento"):
        return ClasificacionGastoSAT.MEDICAMENTO.value
    if clasificacion.get("es_vehiculo"):
        return ClasificacionGastoSAT.VEHICULO.value
    if clasificacion.get("es_activo_fijo"):
        return ClasificacionGastoSAT.ACTIVO_FIJO.value
    return ClasificacionGastoSAT.NORMAL.value


# ============================================================
# FUNCIÓN PRINCIPAL DE CLASIFICACIÓN
# ============================================================
async def clasificar_factura(
    db: AsyncSession,
    factura: FacturaElectronica,
) -> dict[str, Any]:
    """
    Calcula todos los campos de clasificación para una factura.

    Estrategia:
      1. Intenta clasificar por impuestos especiales (más preciso)
      2. Si no hay impuestos especiales, usa heurística por descripción
      3. Combina con clasificación por tipo de documento y régimen fiscal

    Args:
        db: Sesión de base de datos
        factura: Objeto FacturaElectronica con relaciones cargadas
                 (detalles, impuestos_especiales)

    Returns:
        Dict con todos los campos de clasificación + clasificacion_gasto_sat_derived
    """
    # 1. Clasificar por región destino
    region_destino = clasificar_region_destino(
        factura.pais_destino_exportacion,
        factura.es_exportacion,
        factura.es_importacion,
    )

    # 2. Clasificar bien/servicio predominante
    detalles = getattr(factura, "detalles", []) or []
    bien_o_servicio_predominante = clasificar_bien_o_servicio_predominante(detalles)

    # 3. Clasificar por impuestos especiales (PRIORIDAD 1)
    impuestos_especiales = getattr(factura, "impuestos_especiales", []) or []
    clasificacion_impuestos = clasificar_por_impuestos_especiales(impuestos_especiales)

    # 4. Si no hay impuestos especiales, usar heurística (PRIORIDAD 2)
    if not impuestos_especiales:
        clasificacion_heuristica = clasificar_por_heuristica_descripcion(detalles)
        # Combinar: si la heurística detecta algo, usarlo
        for key in ("es_medicamento", "es_vehiculo", "es_combustible", "es_activo_fijo"):
            if clasificacion_heuristica[key]:
                clasificacion_impuestos[key] = True
                logger.debug(
                    f"Factura {factura.id}: {key} detectado por heurística de descripción"
                )

    # 5. Clasificar por tipo de documento
    clasificacion_tipo_doc = clasificar_tipo_documento(factura.tipo_documento)

    # 6. Clasificar pequeño contribuyente (requiere query adicional)
    es_pequeno_contribuyente = await clasificar_pequeno_contribuyente(
        db,
        factura.emisor_nit,
        factura.empresa_id,
    )

    # 7. Vehículos usados vs nuevos (placeholder - requiere lógica adicional del XML)
    es_vehiculo_usado = False
    es_vehiculo_nuevo = False
    if clasificacion_impuestos["es_vehiculo"]:
        # TODO: Determinar si es usado o nuevo según año de fabricación del XML FEL
        pass

    # 8. No genera crédito fiscal (placeholder - requiere lógica adicional)
    no_genera_credito_fiscal = False
    # TODO: Implementar lógica para determinar si no genera crédito fiscal

    # 9. Derivar clasificacion_gasto_sat desde los booleanos
    clasificacion_gasto_sat_derived = derivar_clasificacion_gasto_sat(clasificacion_impuestos)

    return {
        "es_medicamento": clasificacion_impuestos["es_medicamento"],
        "es_vehiculo": clasificacion_impuestos["es_vehiculo"],
        "es_vehiculo_usado": es_vehiculo_usado,
        "es_vehiculo_nuevo": es_vehiculo_nuevo,
        "es_pequeno_contribuyente": es_pequeno_contribuyente,
        "es_no_afecta": clasificacion_tipo_doc["es_no_afecta"],
        "no_genera_credito_fiscal": no_genera_credito_fiscal,
        "tiene_constancia_exencion": clasificacion_tipo_doc["tiene_constancia_exencion"],
        "region_destino": region_destino,
        "bien_o_servicio_predominante": bien_o_servicio_predominante,
        # Campo derivado (útil para debug y trazabilidad)
        "clasificacion_gasto_sat_derived": clasificacion_gasto_sat_derived,
    }


# ============================================================
# HELPER PARA INGESTIÓN FEL
# ============================================================
async def aplicar_clasificacion_a_factura(
    db: AsyncSession,
    factura_id: int,
) -> dict[str, Any] | None:
    """
    Carga una factura con sus relaciones y aplica la clasificación.

    Útil para integrar en el servicio de ingestión FEL.
    Retorna el dict de clasificación aplicada, o None si la factura no existe.
    """
    stmt = (
        select(FacturaElectronica)
        .where(FacturaElectronica.id == factura_id)
        .options(
            selectinload(FacturaElectronica.detalles),
            selectinload(FacturaElectronica.impuestos_especiales)
            .selectinload(FacturaImpuestoEspecial.catalogo),
        )
    )
    result = await db.execute(stmt)
    factura = result.scalar_one_or_none()

    if not factura:
        logger.warning(f"Factura {factura_id} no encontrada para clasificar")
        return None

    clasificacion = await clasificar_factura(db, factura)

    # Filtrar campos derivados (no existen en el modelo)
    CAMPOS_DERIVADOS = {"clasificacion_gasto_sat_derived"}
    clasificacion_aplicable = {
        k: v for k, v in clasificacion.items()
        if k not in CAMPOS_DERIVADOS and hasattr(factura, k)
    }

    for campo, valor in clasificacion_aplicable.items():
        setattr(factura, campo, valor)

    await db.flush()
    logger.info(
        f"✅ Factura {factura_id} clasificada: "
        f"region={clasificacion['region_destino']}, "
        f"medicamento={clasificacion['es_medicamento']}, "
        f"vehiculo={clasificacion['es_vehiculo']}, "
        f"pc={clasificacion['es_pequeno_contribuyente']}, "
        f"b_o_s={clasificacion['bien_o_servicio_predominante']}, "
        f"derived={clasificacion['clasificacion_gasto_sat_derived']}"
    )

    return clasificacion
