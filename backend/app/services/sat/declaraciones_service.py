"""
Servicio de Declaraciones de Impuestos – Motor de Cálculo Dinámico SAT-2237

Flujo:
  1. Cargar formulario + secciones + casillas + reglas + exclusiones desde BD
  2. Cargar facturas FEL del período
  3. Calcular casillas con reglas de filtrado (SUMA / CONTEO)
  4. Evaluar fórmulas ({3.1} + {3.2} * 0.12, CASE WHEN, etc.)
  5. Persistir DeclaracionImpuesto + DetalleDeclaracionImpuesto + DeclaracionImpuestoFactura
"""

import logging
import re
from datetime import date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.global_models import (
    CasillaSat,
    ExclusionCasilla,
    FormularioSat,
    ReglaFiltradoFactura,
    SeccionFormulario,
)
from app.models.tenant_models import (
    DeclaracionImpuesto,
    DeclaracionImpuestoFactura,
    DetalleDeclaracionImpuesto,
    FacturaElectronica,
)

logger = logging.getLogger(__name__)

# ============================================================
# CONSTANTES
# ============================================================
CODIGO_FORMULARIO_SAT_2237 = "SAT-2237"
MAX_ITERACIONES_FORMULA = 20
PATRON_REFERENCIA = re.compile(r"\{([^}]+)\}")

# Campos numéricos de FacturaElectronica que se pueden usar en campo_factura
CAMPOS_NUMERICOS_FACTURA = {
    "total_gravado_gtq", "total_iva_gtq", "total_exento_gtq", "total_gtq",
    "total_gravado_bienes_gtq", "total_iva_bienes_gtq",
    "total_gravado_servicios_gtq", "total_iva_servicios_gtq",
    "total_gravado", "total_iva", "total_exento", "total",
    "retencion_iva", "retencion_isr",
}


# ============================================================
# HELPERS
# ============================================================
def redondear_entero(valor: Decimal | float | int | None) -> int:
    """Redondea a entero (el formulario SAT usa Q enteros)."""
    if valor is None:
        return 0
    try:
        return int(Decimal(str(valor)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except (InvalidOperation, ValueError):
        return 0


def _obtener_campo(factura: FacturaElectronica, campo: str) -> Any:
    """Obtiene un campo de la factura de forma segura."""
    return getattr(factura, campo, None)


# ============================================================
# MOTOR DE CRITERIOS (criterios_json / criterios_exclusion_json)
# ============================================================
def factura_cumple_criterios(factura: FacturaElectronica, criterios: dict) -> bool:
    """
    Evalúa si una factura cumple TODOS los criterios (AND implícito).

    Operadores soportados: $gt, $gte, $lt, $lte, $ne, $in, $not_in, $is_null
    """
    if not criterios:
        return True

    for campo, condicion in criterios.items():
        valor = _obtener_campo(factura, campo)

        # --- dict con operadores ---
        if isinstance(condicion, dict):
            if "$gt" in condicion and not (valor is not None and valor > condicion["$gt"]):
                return False
            if "$gte" in condicion and not (valor is not None and valor >= condicion["$gte"]):
                return False
            if "$lt" in condicion and not (valor is not None and valor < condicion["$lt"]):
                return False
            if "$lte" in condicion and not (valor is not None and valor <= condicion["$lte"]):
                return False
            if "$ne" in condicion and valor == condicion["$ne"]:
                return False
            if "$not_in" in condicion and valor in condicion["$not_in"]:
                return False
            if "$in" in condicion and valor not in condicion["$in"]:
                return False
            if "$is_null" in condicion:
                if condicion["$is_null"] and valor is not None:
                    return False
                if not condicion["$is_null"] and valor is None:
                    return False
            continue

        # --- lista → IN ---
        if isinstance(condicion, list):
            if valor not in condicion:
                return False
            continue

        # --- null → IS NULL ---
        if condicion is None:
            if valor is not None:
                return False
            continue

        # --- igualdad simple ---
        if valor != condicion:
            return False

    return True


def factura_cumple_exclusion(factura: FacturaElectronica, exclusiones: list[dict]) -> bool:
    """Retorna True si la factura debe ser EXCLUIDA (cumple alguna exclusión)."""
    for exc_criterios in exclusiones:
        if factura_cumple_criterios(factura, exc_criterios):
            return True
    return False


# ============================================================
# EVALUADOR DE FÓRMULAS (con soporte CASE WHEN)
# ============================================================
def _convertir_case_when(expresion: str, valores: dict[str, Decimal]) -> str:
    """
    Convierte sintaxis SQL CASE WHEN a expresión Python.

    Ejemplo:
      "CASE WHEN {5_SUM} > {3_SUM} THEN {5_SUM} - {3_SUM} ELSE 0 END"
      → "(({5_SUM}) - ({3_SUM}) if ({5_SUM}) > ({3_SUM}) else 0)"
    """
    # Reemplazar referencias {codigo} por valores envueltos en paréntesis
    def wrap_ref(match: re.Match) -> str:
        codigo = match.group(1).strip()
        val = valores.get(codigo, Decimal("0"))
        return f"({val})"

    expr = PATRON_REFERENCIA.sub(wrap_ref, expresion)

    # Patrón: CASE WHEN <cond> THEN <val_si> ELSE <val_no> END
    patron_case = re.compile(
        r"CASE\s+WHEN\s+(.+?)\s+THEN\s+(.+?)\s+ELSE\s+(.+?)\s+END",
        re.IGNORECASE | re.DOTALL,
    )

    def reemplazar_case(match: re.Match) -> str:
        cond = match.group(1).strip()
        val_si = match.group(2).strip()
        val_no = match.group(3).strip()
        # Convertir operadores SQL a Python
        cond_py = cond.replace(">", ">").replace("<", "<")
        return f"(({val_si}) if ({cond_py}) else ({val_no}))"

    expr = patron_case.sub(reemplazar_case, expr)
    return expr


def evaluar_formula(
    formula: str,
    valores: dict[str, Decimal],
) -> Decimal:
    """
    Evalúa una fórmula tipo '{3.1} + {3.2} + {3.4}' o '{5.12} * 0.12'
    o 'CASE WHEN {5_SUM} > {3_SUM} THEN {5_SUM} - {3_SUM} ELSE 0 END'.
    """
    if not formula:
        return Decimal("0")

    # Primero convertir CASE WHEN
    expresion = _convertir_case_when(formula, valores)

    # Luego reemplazar referencias restantes (si no había CASE WHEN)
    def reemplazar_ref(match: re.Match) -> str:
        codigo = match.group(1).strip()
        val = valores.get(codigo, Decimal("0"))
        return str(val)

    expresion = PATRON_REFERENCIA.sub(reemplazar_ref, expresion)

    try:
        resultado = eval(  # noqa: S307
            expresion,
            {"__builtins__": {}},
            {"max": lambda *a: max(*a), "min": lambda *a: min(*a), "Decimal": Decimal},
        )
        return Decimal(str(resultado))
    except Exception as e:
        logger.warning(f"No se pudo evaluar fórmula '{formula}' → '{expresion}': {e}")
        return Decimal("0")


# ============================================================
# MOTOR DE CÁLCULO POR CASILLA (desde reglas de BD)
# ============================================================
def calcular_casilla_con_reglas(
    facturas: list[FacturaElectronica],
    reglas: list[ReglaFiltradoFactura],
    exclusiones: list[ExclusionCasilla],
) -> tuple[Decimal, Decimal, list[int]]:
    """
    Calcula el valor de una casilla aplicando sus reglas de filtrado y exclusiones.
    Retorna: (base_calculada, impuesto_calculado, ids_facturas_asociadas)
    """
    base_total = Decimal("0.00")
    impuesto_total = Decimal("0.00")
    facturas_ids: list[int] = []

    exc_criterios_list = [
        exc.criterios_exclusion_json
        for exc in exclusiones
        if getattr(exc, "es_activa", True) and exc.criterios_exclusion_json
    ]

    reglas_ordenadas = sorted(reglas, key=lambda r: r.orden or 0)

    for regla in reglas_ordenadas:
        if not getattr(regla, "es_activa", True):
            continue

        criterios = regla.criterios_json or {}
        campo = regla.campo_factura
        operacion = (regla.operacion or "SUMA").upper()

        for f in facturas:
            try:
                if not factura_cumple_criterios(f, criterios):
                    continue
                if exc_criterios_list and factura_cumple_exclusion(f, exc_criterios_list):
                    continue

                facturas_ids.append(f.id)

                if operacion == "CONTEO":
                    base_total += Decimal("1")
                elif operacion in ("SUMA", "PROMEDIO"):
                    if campo and campo in CAMPOS_NUMERICOS_FACTURA:
                        valor = getattr(f, campo, None)
                        if valor is not None:
                            base_total += Decimal(str(valor))
                elif operacion == "SUMA_BASE_E_IMPUESTO":
                    if campo and "|" in campo:
                        campo_base, campo_imp = campo.split("|", 1)
                        base_total += Decimal(str(getattr(f, campo_base, 0) or 0))
                        impuesto_total += Decimal(str(getattr(f, campo_imp, 0) or 0))
                    elif campo:
                        base_total += Decimal(str(getattr(f, campo, 0) or 0))

            except Exception as e:
                logger.error(f"Error procesando factura {f.id} en regla '{regla.nombre}': {e}")
                continue

    if reglas_ordenadas and reglas_ordenadas[0].operacion == "PROMEDIO" and len(facturas_ids) > 0:
        base_total = base_total / Decimal(str(len(facturas_ids)))

    return base_total, impuesto_total, facturas_ids


# ============================================================
# FUNCIÓN PRINCIPAL: GENERAR FORMULARIO SOMBRA
# ============================================================
async def generar_formulario_sombra(
    db: AsyncSession,
    empresa_id: int,
    anio: int,
    mes: int,
    codigo_formulario: str = CODIGO_FORMULARIO_SAT_2237,
    usuario_id: int | None = None,
) -> dict:
    """
    Genera (o regenera) la declaración sombra del SAT-2237 para un período.
    Usa los campos reales del modelo:
      - DeclaracionImpuesto: formulario_sat_id, anio, mes
      - DetalleDeclaracionImpuesto: casilla_sat_id, base_imponible, monto_impuesto
      - DeclaracionImpuestoFactura: detalle_declaracion_id, factura_id, base_asignada, impuesto_asignado
    """

    # ================================================================
    # PASO 1: Cargar formulario SAT-2237
    # ================================================================
    stmt_form = select(FormularioSat).where(
        FormularioSat.codigo == codigo_formulario,
        FormularioSat.es_version_activa.is_(True),
    )
    formulario = (await db.execute(stmt_form)).scalar_one_or_none()
    if formulario is None:
        raise ValueError(f"Formulario {codigo_formulario} no encontrado en BD. Ejecutar seed.")

    # ================================================================
    # PASO 2: Cargar secciones + casillas + reglas + exclusiones
    # ================================================================
    stmt_secciones = (
        select(SeccionFormulario)
        .where(SeccionFormulario.formulario_id == formulario.id)
        .options(
            selectinload(SeccionFormulario.casillas)
            .selectinload(CasillaSat.reglas_filtrado),
            selectinload(SeccionFormulario.casillas)
            .selectinload(CasillaSat.exclusiones),
        )
        .order_by(SeccionFormulario.numero_seccion, SeccionFormulario.orden)
    )
    secciones = list((await db.execute(stmt_secciones)).scalars().unique().all())

    if not secciones:
        raise ValueError(f"Formulario {codigo_formulario} no tiene secciones configuradas.")

    # Aplanar casillas y construir índices
    todas_casillas: list[CasillaSat] = []
    casilla_por_codigo: dict[str, CasillaSat] = {}
    for sec in secciones:
        for cas in sorted(sec.casillas, key=lambda c: c.orden_seccion or 0):
            todas_casillas.append(cas)
            casilla_por_codigo[cas.codigo] = cas

    logger.info(f"SAT-2237: {len(secciones)} secciones, {len(todas_casillas)} casillas cargadas")

    # ================================================================
    # PASO 3: Cargar facturas FEL del período
    # ================================================================
    fecha_inicio = date(anio, mes, 1)
    if mes == 12:
        fecha_fin = date(anio + 1, 1, 1)
    else:
        fecha_fin = date(anio, mes + 1, 1)

    stmt_facturas = (
        select(FacturaElectronica)
        .where(
            FacturaElectronica.empresa_id == empresa_id,
            FacturaElectronica.fecha_emision >= fecha_inicio,
            FacturaElectronica.fecha_emision < fecha_fin,
            FacturaElectronica.estado != "ANULADA",
        )
        .order_by(FacturaElectronica.fecha_emision)
    )
    todas_facturas = list((await db.execute(stmt_facturas)).scalars().all())
    logger.info(
        f"SAT-2237: {len(todas_facturas)} facturas para empresa {empresa_id}, "
        f"período {anio}-{mes:02d}"
    )

    # ================================================================
    # PASO 4: Verificar / crear declaración (campos REALES del modelo)
    # ================================================================
    stmt_decl = select(DeclaracionImpuesto).where(
        DeclaracionImpuesto.empresa_id == empresa_id,
        DeclaracionImpuesto.formulario_sat_id == formulario.id,
        DeclaracionImpuesto.anio == anio,
        DeclaracionImpuesto.mes == mes,
    )
    declaracion = (await db.execute(stmt_decl)).scalar_one_or_none()

    if declaracion is not None:
        if declaracion.estado == "FINALIZADO":
            raise ValueError(
                f"La declaración de {anio}-{mes:02d} ya está finalizada. "
                "No se puede regenerar."
            )
        # Limpiar detalles y asociaciones previas
        stmt_del_det = select(DetalleDeclaracionImpuesto).where(
            DetalleDeclaracionImpuesto.declaracion_id == declaracion.id
        )
        for det in (await db.execute(stmt_del_det)).scalars().all():
            await db.delete(det)
        await db.flush()
        declaracion.estado = "BORRADOR"
    else:
        # Calcular remanente del período anterior
        remanente_anterior = Decimal("0.00")
        mes_ant = mes - 1 if mes > 1 else 12
        anio_ant = anio if mes > 1 else anio - 1
        stmt_rem = select(DeclaracionImpuesto.remanente_siguiente_periodo).where(
            DeclaracionImpuesto.empresa_id == empresa_id,
            DeclaracionImpuesto.formulario_sat_id == formulario.id,
            DeclaracionImpuesto.anio == anio_ant,
            DeclaracionImpuesto.mes == mes_ant,
            DeclaracionImpuesto.estado == "FINALIZADO",
        )
        rem_val = (await db.execute(stmt_rem)).scalar_one_or_none()
        if rem_val:
            remanente_anterior = Decimal(str(rem_val))

        declaracion = DeclaracionImpuesto(
            empresa_id=empresa_id,
            formulario_sat_id=formulario.id,
            anio=anio,
            mes=mes,
            estado="BORRADOR",
            remanente_periodo_anterior=remanente_anterior,
        )
        db.add(declaracion)
        await db.flush()

    # ================================================================
    # PASO 5: CALCULAR CASILLAS CON REGLAS DE FILTRADO
    # ================================================================
    valores: dict[str, Decimal] = {}
    facturas_por_casilla: dict[str, list[int]] = {}

    for casilla in todas_casillas:
        reglas_activas = [r for r in (casilla.reglas_filtrado or []) if getattr(r, "es_activa", True)]
        if not reglas_activas:
            continue

        base, impuesto, fac_ids = calcular_casilla_con_reglas(
            facturas=todas_facturas,
            reglas=reglas_activas,
            exclusiones=casilla.exclusiones or [],
        )

        tipo = (casilla.tipo_casilla or "").upper()
        if tipo == "CONTEO":
            valores[casilla.codigo] = base
        else:
            valores[casilla.codigo] = base

        facturas_por_casilla[casilla.codigo] = fac_ids

    logger.info(f"SAT-2237: {len(valores)} casillas calculadas con reglas de filtrado")

    # ================================================================
    # PASO 6: EVALUAR FÓRMULAS (con soporte CASE WHEN)
    # ================================================================
    casillas_con_formula = [
        c for c in todas_casillas
        if c.formula_calculo and c.codigo not in valores
    ]

    for _iter in range(MAX_ITERACIONES_FORMULA):
        calculadas_en_iter = 0
        for casilla in list(casillas_con_formula):
            refs = PATRON_REFERENCIA.findall(casilla.formula_calculo)
            if all(ref.strip() in valores for ref in refs):
                valores[casilla.codigo] = evaluar_formula(casilla.formula_calculo, valores)
                casillas_con_formula.remove(casilla)
                calculadas_en_iter += 1

        if not casillas_con_formula:
            break
        if calculadas_en_iter == 0:
            codigos_pendientes = [c.codigo for c in casillas_con_formula]
            logger.warning(
                f"SAT-2237: No se pudieron resolver fórmulas (iter {_iter}): "
                f"{codigos_pendientes}"
            )
            for c in casillas_con_formula:
                valores[c.codigo] = Decimal("0")
            break

    logger.info(f"SAT-2237: Fórmulas resueltas en {_iter + 1} iteración(es)")

    # ================================================================
    # PASO 7: INICIALIZAR CASILLAS SIN VALOR EN 0
    # ================================================================
    for casilla in todas_casillas:
        if casilla.codigo not in valores:
            valores[casilla.codigo] = Decimal("0")

    # ================================================================
    # PASO 8: PERSISTIR DETALLES Y ASOCIACIONES (campos REALES)
    # ================================================================
    # Mapa: codigo → DetalleDeclaracionImpuesto creado
    detalles_creados: dict[str, DetalleDeclaracionImpuesto] = {}

    for casilla in todas_casillas:
        valor_raw = valores.get(casilla.codigo, Decimal("0"))
        tipo = (casilla.tipo_casilla or "").upper()

        # Decidir dónde va el valor según tipo_casilla
        if tipo in ("BASE_IMPONIBLE", "REFERENCIA", "CONTEO"):
            base_val = valor_raw
            imp_val = Decimal("0")
        elif tipo in ("DEBITO_FISCAL", "CREDITO_FISCAL", "CALCULADO", "AJUSTE", "REMANENTE"):
            base_val = Decimal("0")
            imp_val = valor_raw
        else:
            base_val = valor_raw
            imp_val = Decimal("0")

        detalle = DetalleDeclaracionImpuesto(
            declaracion_id=declaracion.id,
            casilla_sat_id=casilla.id,
            base_imponible=redondear_entero(base_val),
            monto_impuesto=redondear_entero(imp_val),
            es_ajuste_manual=False,
        )
        db.add(detalle)
        await db.flush()  # Necesario para obtener detalle.id
        detalles_creados[casilla.codigo] = detalle

        # DeclaracionImpuestoFactura (asociaciones)
        fac_ids = facturas_por_casilla.get(casilla.codigo, [])
        for fid in fac_ids:
            # Obtener valores asignados de la factura
            factura_obj = next((f for f in todas_facturas if f.id == fid), None)
            base_asig = Decimal("0")
            imp_asig = Decimal("0")
            if factura_obj:
                # Buscar la regla que aplicó para obtener el campo correcto
                for regla in (casilla.reglas_filtrado or []):
                    if not getattr(regla, "es_activa", True):
                        continue
                    if factura_cumple_criterios(factura_obj, regla.criterios_json or {}):
                        campo = regla.campo_factura
                        if campo and campo in CAMPOS_NUMERICOS_FACTURA:
                            base_asig = Decimal(str(getattr(factura_obj, campo, 0) or 0))
                        break

            db.add(
                DeclaracionImpuestoFactura(
                    detalle_declaracion_id=detalle.id,
                    factura_id=fid,
                    base_asignada=base_asig,
                    impuesto_asignado=imp_asig,
                )
            )

    # ================================================================
    # PASO 9: CALCULAR TOTALES DE LA DECLARACIÓN
    # ================================================================
    # Débito fiscal: suma de monto_impuesto de casillas tipo DEBITO_FISCAL
    # Crédito fiscal: suma de monto_impuesto de casillas tipo CREDITO_FISCAL
    total_debito = Decimal("0")
    total_credito = Decimal("0")

    for casilla in todas_casillas:
        tipo = (casilla.tipo_casilla or "").upper()
        val = valores.get(casilla.codigo, Decimal("0"))
        if tipo == "DEBITO_FISCAL":
            total_debito += val
        elif tipo == "CREDITO_FISCAL":
            total_credito += val

    remanente_anterior = valores.get("5_REM", Decimal("0"))
    impuesto_determinado = max(Decimal("0"), total_debito - total_credito - remanente_anterior)
    remanente_siguiente = max(
        Decimal("0"),
        total_credito + remanente_anterior - total_debito,
    )
    impuesto_a_pagar = impuesto_determinado

    declaracion.total_debito_fiscal = redondear_entero(total_debito)
    declaracion.total_credito_fiscal = redondear_entero(total_credito)
    declaracion.impuesto_determinado = redondear_entero(impuesto_determinado)
    declaracion.remanente_periodo_anterior = redondear_entero(remanente_anterior)
    declaracion.remanente_siguiente_periodo = redondear_entero(remanente_siguiente)
    declaracion.impuesto_a_pagar = redondear_entero(impuesto_a_pagar)

    await db.commit()

    logger.info(
        f"SAT-2237: Declaración {declaracion.id} generada → "
        f"Débito={declaracion.total_debito_fiscal}, "
        f"Crédito={declaracion.total_credito_fiscal}, "
        f"Impuesto={declaracion.impuesto_a_pagar}"
    )

    return {
        "mensaje": "Formulario sombra generado exitosamente",
        "declaracion_id": declaracion.id,
        "estado": declaracion.estado,
        "totales": {
            "debito_fiscal": redondear_entero(total_debito),
            "credito_fiscal": redondear_entero(total_credito),
            "remanente_anterior": redondear_entero(remanente_anterior),
            "impuesto_determinado": redondear_entero(impuesto_determinado),
            "impuesto_a_pagar": redondear_entero(impuesto_a_pagar),
            "remanente_siguiente": redondear_entero(remanente_siguiente),
        },
        "casillas_calculadas": len(valores),
        "facturas_procesadas": len(todas_facturas),
    }


# ============================================================
# OBTENER DECLARACIÓN CON DETALLES
# ============================================================
async def obtener_declaracion(db: AsyncSession, declaracion_id: int) -> dict | None:
    """Obtiene una declaración con todos sus detalles."""
    stmt = (
        select(DeclaracionImpuesto)
        .where(DeclaracionImpuesto.id == declaracion_id)
        .options(
            selectinload(DeclaracionImpuesto.detalles)
            .selectinload(DetalleDeclaracionImpuesto.casilla)
            .selectinload(CasillaSat.seccion_rel),
        )
    )
    declaracion = (await db.execute(stmt)).scalar_one_or_none()
    if declaracion is None:
        return None

    detalles_out = []
    for det in declaracion.detalles:
        casilla = det.casilla
        detalles_out.append({
            "id": det.id,
            "casilla_codigo": casilla.codigo if casilla else "",
            "casilla_nombre": casilla.nombre if casilla else "",
            "seccion": casilla.seccion_rel.numero_seccion if casilla and casilla.seccion_rel else "",
            "tipo_casilla": casilla.tipo_casilla if casilla else "",
            "base_imponible": int(det.base_imponible or 0),
            "monto_impuesto": int(det.monto_impuesto or 0),
            "es_ajuste_manual": det.es_ajuste_manual,
            "motivo_ajuste": det.motivo_ajuste,
        })

    # Obtener código del formulario
    stmt_form = select(FormularioSat.codigo).where(
        FormularioSat.id == declaracion.formulario_sat_id
    )
    form_codigo = (await db.execute(stmt_form)).scalar_one_or_none() or ""

    return {
        "id": declaracion.id,
        "empresa_id": declaracion.empresa_id,
        "formulario_codigo": form_codigo,
        "anio": declaracion.anio,
        "mes": declaracion.mes,
        "estado": declaracion.estado,
        "total_debito_fiscal": int(declaracion.total_debito_fiscal or 0),
        "total_credito_fiscal": int(declaracion.total_credito_fiscal or 0),
        "remanente_periodo_anterior": int(declaracion.remanente_periodo_anterior or 0),
        "impuesto_determinado": int(declaracion.impuesto_determinado or 0),
        "remanente_siguiente_periodo": int(declaracion.remanente_siguiente_periodo or 0),
        "impuesto_a_pagar": int(declaracion.impuesto_a_pagar or 0),
        "detalles": detalles_out,
        "created_at": declaracion.created_at.isoformat() if declaracion.created_at else None,
    }


# ============================================================
# FINALIZAR DECLARACIÓN
# ============================================================
async def finalizar_declaracion(
    db: AsyncSession,
    declaracion_id: int,
    usuario_id: int | None = None,
) -> dict:
    stmt = select(DeclaracionImpuesto).where(DeclaracionImpuesto.id == declaracion_id)
    declaracion = (await db.execute(stmt)).scalar_one_or_none()
    if declaracion is None:
        raise ValueError("Declaración no encontrada")
    if declaracion.estado == "FINALIZADO":
        raise ValueError("La declaración ya está finalizada")

    declaracion.estado = "FINALIZADO"
    declaracion.finalizado_por = usuario_id
    declaracion.fecha_cierre = datetime.now(timezone.utc)

    await db.commit()
    return {"mensaje": "Declaración finalizada exitosamente", "declaracion_id": declaracion.id}


# ============================================================
# AJUSTE MANUAL
# ============================================================
async def aplicar_ajuste_manual(
    db: AsyncSession,
    declaracion_id: int,
    casilla_codigo: str,
    base_imponible: Decimal | None = None,
    monto_impuesto: Decimal | None = None,
    motivo_ajuste: str | None = None,
    usuario_id: int | None = None,
) -> dict:
    """Aplica un ajuste manual a una casilla y recalcula totales."""
    stmt = select(DeclaracionImpuesto).where(DeclaracionImpuesto.id == declaracion_id)
    declaracion = (await db.execute(stmt)).scalar_one_or_none()
    if declaracion is None:
        raise ValueError("Declaración no encontrada")
    if declaracion.estado == "FINALIZADO":
        raise ValueError("No se puede ajustar una declaración finalizada")

    # Buscar el detalle por casilla_codigo
    stmt_det = (
        select(DetalleDeclaracionImpuesto)
        .join(CasillaSat, DetalleDeclaracionImpuesto.casilla_sat_id == CasillaSat.id)
        .where(
            DetalleDeclaracionImpuesto.declaracion_id == declaracion_id,
            CasillaSat.codigo == casilla_codigo,
        )
    )
    detalle = (await db.execute(stmt_det)).scalar_one_or_none()
    if detalle is None:
        raise ValueError(f"Casilla {casilla_codigo} no encontrada en la declaración")

    # Verificar que la casilla es editable
    casilla = await db.get(CasillaSat, detalle.casilla_sat_id)
    if casilla and not casilla.es_editable:
        raise ValueError(f"La casilla {casilla_codigo} no es editable")

    # Aplicar ajuste
    if base_imponible is not None:
        detalle.base_imponible = redondear_entero(base_imponible)
    if monto_impuesto is not None:
        detalle.monto_impuesto = redondear_entero(monto_impuesto)
    detalle.es_ajuste_manual = True
    detalle.motivo_ajuste = motivo_ajuste
    detalle.ajustado_por = usuario_id

    # Recalcular totales
    await _recalcular_totales(db, declaracion)

    await db.commit()
    return {"mensaje": "Ajuste manual aplicado y totales recalculados exitosamente"}


async def _recalcular_totales(db: AsyncSession, declaracion: DeclaracionImpuesto) -> None:
    """Recalcula los totales de la declaración a partir de sus detalles."""
    stmt_dets = (
        select(DetalleDeclaracionImpuesto, CasillaSat.tipo_casilla)
        .join(CasillaSat, DetalleDeclaracionImpuesto.casilla_sat_id == CasillaSat.id)
        .where(DetalleDeclaracionImpuesto.declaracion_id == declaracion.id)
    )
    rows = (await db.execute(stmt_dets)).all()

    total_debito = Decimal("0")
    total_credito = Decimal("0")
    remanente_ant = Decimal("0")

    for det, tipo_casilla in rows:
        tipo = (tipo_casilla or "").upper()
        if tipo == "DEBITO_FISCAL":
            total_debito += det.monto_impuesto or Decimal("0")
        elif tipo == "CREDITO_FISCAL":
            total_credito += det.monto_impuesto or Decimal("0")

        # Buscar casilla 5_REM para remanente anterior
        if det.casilla and det.casilla.codigo == "5_REM":
            remanente_ant = det.monto_impuesto or Decimal("0")

    impuesto_det = max(Decimal("0"), total_debito - total_credito - remanente_ant)
    remanente_sig = max(Decimal("0"), total_credito + remanente_ant - total_debito)

    declaracion.total_debito_fiscal = redondear_entero(total_debito)
    declaracion.total_credito_fiscal = redondear_entero(total_credito)
    declaracion.impuesto_determinado = redondear_entero(impuesto_det)
    declaracion.remanente_periodo_anterior = redondear_entero(remanente_ant)
    declaracion.remanente_siguiente_periodo = redondear_entero(remanente_sig)
    declaracion.impuesto_a_pagar = redondear_entero(impuesto_det)


# ============================================================
# DRILL-DOWN: FACTURAS DE UNA CASILLA
# ============================================================
async def obtener_facturas_casilla(
    db: AsyncSession,
    declaracion_id: int,
    casilla_codigo: str,
) -> list[dict]:
    """Obtiene las facturas asociadas a una casilla de la declaración."""
    # Buscar el detalle
    stmt_det = (
        select(DetalleDeclaracionImpuesto.id)
        .join(CasillaSat, DetalleDeclaracionImpuesto.casilla_sat_id == CasillaSat.id)
        .where(
            DetalleDeclaracionImpuesto.declaracion_id == declaracion_id,
            CasillaSat.codigo == casilla_codigo,
        )
    )
    detalle_id = (await db.execute(stmt_det)).scalar_one_or_none()
    if detalle_id is None:
        return []

    # Obtener facturas asociadas
    stmt_fac = (
        select(FacturaElectronica, DeclaracionImpuestoFactura.base_asignada, DeclaracionImpuestoFactura.impuesto_asignado)
        .join(
            DeclaracionImpuestoFactura,
            FacturaElectronica.id == DeclaracionImpuestoFactura.factura_id,
        )
        .where(DeclaracionImpuestoFactura.detalle_declaracion_id == detalle_id)
        .order_by(FacturaElectronica.fecha_emision)
    )
    rows = (await db.execute(stmt_fac)).all()

    resultado = []
    for factura, base_asig, imp_asig in rows:
        resultado.append({
            "factura_id": factura.id,
            "numero": f"{factura.serie or ''}-{factura.numero}",
            "fecha_emision": factura.fecha_emision.strftime("%Y-%m-%d") if factura.fecha_emision else None,
            "tercero": factura.receptor_nombre if factura.tipo_operacion == "Venta" else factura.emisor_nombre,
            "nit": factura.receptor_nit if factura.tipo_operacion == "Venta" else factura.emisor_nit,
            "base_asignada": float(base_asig or 0),
            "impuesto_asignado": float(imp_asig or 0),
        })

    return resultado
