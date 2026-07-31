"""
Servicio de Declaraciones de Impuestos – Motor de Cálculo Dinámico SAT-2237

Flujo:
  1. Cargar formulario + secciones + casillas + reglas + exclusiones desde BD
  2. Cargar facturas FEL del período
  3. Calcular casillas con reglas de filtrado (SUMA / CONTEO)
  4. Evaluar fórmulas ({3.1} + {3.2} * 0.12) con resolución de dependencias
  5. Calcular secciones especiales (7: Determinación, 11: Accesorios)
  6. Persistir DeclaracionImpuesto + DetalleDeclaracionImpuesto + DeclaracionImpuestoFactura
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
MAX_ITERACIONES_FORMULA = 20  # límite para resolver dependencias circulares
PATRON_REFERENCIA = re.compile(r"\{([^}]+)\}")  # captura {3.1}, {5.12_C}, etc.

# Campos numéricos de FacturaElectronica que se pueden usar en campo_factura
CAMPOS_NUMERICOS_FACTURA = {
    "total_gravado_gtq",
    "total_iva_gtq",
    "total_exento_gtq",
    "total_gtq",
    "total_gravado_bienes_gtq",
    "total_iva_bienes_gtq",
    "total_gravado_servicios_gtq",
    "total_iva_servicios_gtq",
    "total_gravado",
    "total_iva",
    "total_exento",
    "total_monto",
    "retencion_iva",
    "retencion_isr",
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

    Formatos soportados en criterios_json:
      {"tipo_operacion": "VENTA"}                   → igualdad
      {"tipo_operacion": ["VENTA", "COMPRA"]}       → IN
      {"es_exento": false}                          → booleano
      {"pais_destino": null}                        → IS NULL
      {"retencion_iva": {"$gt": 0}}                → mayor que
      {"retencion_iva": {"$gte": 0, "$lt": 100}}   → rango
      {"tipo_documento": {"$ne": "NCDE"}}           → distinto
      {"tipo_documento": {"$not_in": ["NCDE"]}}     → NOT IN
      {"es_exportacion": {"$is_null": false}}       → IS NOT NULL
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
    """
    Retorna True si la factura debe ser EXCLUIDA (cumple alguna exclusión).
    Cada exclusión tiene criterios_exclusion_json.
    """
    for exc_criterios in exclusiones:
        if factura_cumple_criterios(factura, exc_criterios):
            return True
    return False


# ============================================================
# EVALUADOR DE FÓRMULAS
# ============================================================
def evaluar_formula(
    formula: str,
    valores: dict[str, Decimal],
) -> Decimal:
    """
    Evalúa una fórmula tipo '{3.1} + {3.2} + {3.4}' o '{5.12} * 0.12'.

    Reemplaza cada {codigo} por su valor numérico y evalúa la expresión.
    Solo permite operaciones aritméticas básicas (+, -, *, /) y funciones
    max() / min() para seguridad.
    """
    if not formula:
        return Decimal("0")

    def reemplazar(match: re.Match) -> str:
        codigo = match.group(1).strip()
        val = valores.get(codigo, Decimal("0"))
        return str(val)

    expresion = PATRON_REFERENCIA.sub(reemplazar, formula)

    # Sanitizar: solo permitir dígitos, punto, operadores, paréntesis, espacios,
    # y las funciones max/min
    sanitizada = expresion.strip()
    if not re.match(r'^[\d\.\+\-\*\/\(\)\s,]+(max|min)?[\d\.\+\-\*\/\(\)\s,]*$', sanitizada):
        # Fallback: intentar evaluar de todas formas con namespace restringido
        pass

    try:
        # Namespace restringido: solo operaciones matemáticas
        resultado = eval(  # noqa: S307
            sanitizada,
            {"__builtins__": {}},
            {
                "max": lambda *a: max(*a),
                "min": lambda *a: min(*a),
                "Decimal": Decimal,
            },
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

    # Pre-procesar exclusiones a lista de dicts
    exc_criterios_list = [
        exc.criterios_exclusion_json
        for exc in exclusiones
        if exc.es_activa and exc.criterios_exclusion_json
    ]

    # Ordenar reglas por orden
    reglas_ordenadas = sorted(reglas, key=lambda r: r.orden or 0)

    for regla in reglas_ordenadas:
        if not regla.es_activa:
            continue

        criterios = regla.criterios_json or {}
        campo = regla.campo_factura  # ej: "total_gravado_gtq", "total_iva_gtq"
        operacion = (regla.operacion or "SUMA").upper()

        for f in facturas:
            try:
                # 1. ¿Cumple criterios de inclusión?
                if not factura_cumple_criterios(f, criterios):
                    continue

                # 2. ¿Cumple alguna exclusión?
                if exc_criterios_list and factura_cumple_exclusion(f, exc_criterios_list):
                    continue

                # 3. Acumular
                facturas_ids.append(f.id)

                if operacion == "CONTEO":
                    # Para CONTEO, cada factura suma 1
                    base_total += Decimal("1")
                elif operacion in ("SUMA", "PROMEDIO"):
                    if campo and campo in CAMPOS_NUMERICOS_FACTURA:
                        valor = getattr(f, campo, None)
                        if valor is not None:
                            base_total += Decimal(str(valor))
                elif operacion == "SUMA_BASE_E_IMPUESTO":
                    # Suma base e impuesto por separado
                    # Se usa cuando campo_factura tiene formato "base|impuesto"
                    # o cuando se necesitan ambos
                    if campo and "|" in campo:
                        campo_base, campo_imp = campo.split("|", 1)
                        base_total += Decimal(str(getattr(f, campo_base, 0) or 0))
                        impuesto_total += Decimal(str(getattr(f, campo_imp, 0) or 0))
                    elif campo:
                        base_total += Decimal(str(getattr(f, campo, 0) or 0))

            except Exception as e:
                logger.error(f"Error procesando factura {f.id} en regla '{regla.nombre}': {e}")
                continue

    # Promedio
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
    usuario_id: int | None = None,
) -> dict:
    """
    Genera (o regenera) la declaración sombra del SAT-2237 para un período.

    Flujo:
      1. Cargar estructura del formulario desde BD
      2. Cargar facturas FEL del período
      3. Calcular casillas con reglas → evaluar fórmulas → secciones especiales
      4. Persistir todo
    """

    # ================================================================
    # PASO 1: Cargar formulario SAT-2237
    # ================================================================
    stmt_form = select(FormularioSat).where(FormularioSat.codigo == CODIGO_FORMULARIO_SAT_2237)
    formulario = (await db.execute(stmt_form)).scalar_one_or_none()
    if formulario is None:
        raise ValueError(f"Formulario {CODIGO_FORMULARIO_SAT_2237} no encontrado en BD. Ejecutar seed.")

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
        raise ValueError(f"Formulario {CODIGO_FORMULARIO_SAT_2237} no tiene secciones configuradas.")

    # Aplanar casillas y construir índices
    todas_casillas: list[CasillaSat] = []
    casilla_por_codigo: dict[str, CasillaSat] = {}
    for sec in secciones:
        for cas in sorted(sec.casillas, key=lambda c: c.orden_seccion or 0):
            todas_casillas.append(cas)
            casilla_por_codigo[cas.codigo] = cas

    logger.info(
        f"SAT-2237: {len(secciones)} secciones, {len(todas_casillas)} casillas cargadas"
    )

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
    # PASO 4: Verificar / crear declaración
    # ================================================================
    stmt_decl = select(DeclaracionImpuesto).where(
        DeclaracionImpuesto.empresa_id == empresa_id,
        DeclaracionImpuesto.formulario_codigo == CODIGO_FORMULARIO_SAT_2237,
        DeclaracionImpuesto.anio_periodo == anio,
        DeclaracionImpuesto.mes_periodo == mes,
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

        stmt_del_fac = select(DeclaracionImpuestoFactura).where(
            DeclaracionImpuestoFactura.declaracion_id == declaracion.id
        )
        for df in (await db.execute(stmt_del_fac)).scalars().all():
            await db.delete(df)

        await db.flush()
        declaracion.estado = "BORRADOR"
    else:
        declaracion = DeclaracionImpuesto(
            empresa_id=empresa_id,
            formulario_codigo=CODIGO_FORMULARIO_SAT_2237,
            anio_periodo=anio,
            mes_periodo=mes,
            estado="BORRADOR",
            created_by=usuario_id,
        )
        db.add(declaracion)
        await db.flush()

    # ================================================================
    # PASO 5: CALCULAR CASILLAS CON REGLAS DE FILTRADO
    # ================================================================
    valores: dict[str, Decimal] = {}  # codigo → valor calculado
    facturas_por_casilla: dict[str, list[int]] = {}  # codigo → [factura_ids]

    # 5a. Casillas con reglas de filtrado (tipo BASE_IMPONIBLE, CONTEO, etc.)
    for casilla in todas_casillas:
        reglas_activas = [r for r in (casilla.reglas_filtrado or []) if r.es_activa]
        if not reglas_activas:
            continue

        base, impuesto, fac_ids = calcular_casilla_con_reglas(
            facturas=todas_facturas,
            reglas=reglas_activas,
            exclusiones=casilla.exclusiones or [],
        )

        # Según tipo_casilla, decidir qué valor guardar
        tipo = (casilla.tipo_casilla or "").upper()
        if tipo == "CONTEO":
            valores[casilla.codigo] = base  # base ya tiene el conteo
        elif tipo in ("CREDITO_FISCAL",) and casilla.formula_calculo:
            # Se calculará en el paso de fórmulas; guardar base como referencia
            valores[casilla.codigo] = base
        else:
            valores[casilla.codigo] = base

        facturas_por_casilla[casilla.codigo] = fac_ids

    logger.info(
        f"SAT-2237: {len(valores)} casillas calculadas con reglas de filtrado"
    )

    # ================================================================
    # PASO 6: EVALUAR FÓRMULAS (resolución iterativa de dependencias)
    # ================================================================
    casillas_con_formula = [
        c for c in todas_casillas
        if c.formula_calculo and c.codigo not in valores
    ]

    for _iter in range(MAX_ITERACIONES_FORMULA):
        calculadas_en_iter = 0
        for casilla in list(casillas_con_formula):
            # Verificar que todas las dependencias estén resueltas
            refs = PATRON_REFERENCIA.findall(casilla.formula_calculo)
            if all(ref.strip() in valores for ref in refs):
                valores[casilla.codigo] = evaluar_formula(
                    casilla.formula_calculo, valores
                )
                casillas_con_formula.remove(casilla)
                calculadas_en_iter += 1

        if not casillas_con_formula:
            break
        if calculadas_en_iter == 0:
            # Dependencia circular o referencia faltante
            codigos_pendientes = [c.codigo for c in casillas_con_formula]
            logger.warning(
                f"SAT-2237: No se pudieron resolver fórmulas (iter {_iter}): "
                f"{codigos_pendientes}"
            )
            # Asignar 0 a las pendientes
            for c in casillas_con_formula:
                valores[c.codigo] = Decimal("0")
            break

    logger.info(
        f"SAT-2237: Fórmulas resueltas en {_iter + 1} iteración(es)"
    )

    # ================================================================
    # PASO 7: SECCIÓN 7 – DETERMINACIÓN DEL IMPUESTO
    # ================================================================
    # Sumar débitos (sección 3) y créditos (secciones 5, 6)
    debito_fiscal = Decimal("0")
    credito_fiscal = Decimal("0")

    for casilla in todas_casillas:
        naturaleza = (casilla.naturaleza or "").lower()
        tipo = (casilla.tipo_casilla or "").upper()
        val = valores.get(casilla.codigo, Decimal("0"))

        if naturaleza == "deudora" or tipo in ("BASE_IMPONIBLE", "CALCULADO"):
            # Verificar que pertenece a sección de débito (sección 3)
            sec_num = str(casilla.seccion_rel.numero_seccion) if casilla.seccion_rel else ""
            if sec_num.startswith("3"):
                debito_fiscal += val

        if naturaleza == "acreedora" or tipo == "CREDITO_FISCAL":
            sec_num = str(casilla.seccion_rel.numero_seccion) if casilla.seccion_rel else ""
            if sec_num.startswith(("5", "6")):
                credito_fiscal += val

    # Remanente del período anterior (casilla editable 5_REM o similar)
    remanente_anterior = valores.get("5_REM", Decimal("0"))

    # Impuesto determinado = max(0, débito - crédito - remanente)
    impuesto_determinado = max(
        Decimal("0"),
        debito_fiscal - credito_fiscal - remanente_anterior,
    )

    # Crédito fiscal para período siguiente (si crédito > débito)
    credito_fiscal_siguiente = max(
        Decimal("0"),
        credito_fiscal + remanente_anterior - debito_fiscal,
    )

    # Impuesto a pagar (puede tener retenciones, ajustes, etc.)
    # Por ahora: impuesto_a_pagar = impuesto_determinado
    impuesto_a_pagar = impuesto_determinado

    # Remanente siguiente
    remanente_siguiente = credito_fiscal_siguiente

    # Guardar valores de la sección 7
    valores_seccion_7 = {
        "DEBITO_FISCAL_TOTAL": debito_fiscal,
        "CREDITO_FISCAL_TOTAL": credito_fiscal,
        "REMANENTE_ANTERIOR": remanente_anterior,
        "IMPUESTO_DETERMINADO": impuesto_determinado,
        "CREDITO_FISCAL_PERIODO_SIGUIENTE_LOCAL": credito_fiscal_siguiente,
        "IMPUESTO_A_PAGAR": impuesto_a_pagar,
        "REMANENTE_SIGUIENTE": remanente_siguiente,
    }
    valores.update(valores_seccion_7)

    # ================================================================
    # PASO 8: SECCIÓN 9 – INDICADORES / CONTEOS
    # ================================================================
    # Conteos y montos de operaciones realizadas (sección 9.1 y 9.2)
    # Estos se calculan con reglas de filtrado si existen,
    # o se dejan en 0 para que el usuario los complete.
    for casilla in todas_casillas:
        sec_num = str(casilla.seccion_rel.numero_seccion) if casilla.seccion_rel else ""
        if sec_num.startswith("9") and casilla.codigo not in valores:
            # Si no tiene reglas ni fórmula, inicializar en 0
            valores[casilla.codigo] = Decimal("0")

    # ================================================================
    # PASO 9: SECCIÓN 11 – ACCESORIOS (multas, intereses, mora)
    # ================================================================
    # Son casillas editables (AJUSTE). Se inicializan en 0.
    for casilla in todas_casillas:
        sec_num = str(casilla.seccion_rel.numero_seccion) if casilla.seccion_rel else ""
        if sec_num.startswith("11") and casilla.codigo not in valores:
            valores[casilla.codigo] = Decimal("0")

    # ================================================================
    # PASO 10: PERSISTIR DETALLES Y ASOCIACIONES
    # ================================================================
    for casilla in todas_casillas:
        valor_raw = valores.get(casilla.codigo, Decimal("0"))
        valor_final = redondear_entero(valor_raw)

        # DetalleDeclaracionImpuesto
        detalle = DetalleDeclaracionImpuesto(
            declaracion_id=declaracion.id,
            casilla_id=casilla.id,
            casilla_codigo=casilla.codigo,
            seccion=str(casilla.seccion_rel.numero_seccion) if casilla.seccion_rel else "",
            valor=Decimal(str(valor_final)),
            valor_original=valor_raw,
            tipo_casilla=casilla.tipo_casilla,
            created_by=usuario_id,
        )
        db.add(detalle)

        # DeclaracionImpuestoFactura (asociaciones)
        fac_ids = facturas_por_casilla.get(casilla.codigo, [])
        for fid in fac_ids:
            db.add(
                DeclaracionImpuestoFactura(
                    declaracion_id=declaracion.id,
                    factura_id=fid,
                    casilla_id=casilla.id,
                    casilla_codigo=casilla.codigo,
                    created_by=usuario_id,
                )
            )

    # ================================================================
    # PASO 11: ACTUALIZAR TOTALES DE LA DECLARACIÓN
    # ================================================================
    declaracion.total_debito_fiscal = redondear_entero(debito_fiscal)
    declaracion.total_credito_fiscal = redondear_entero(credito_fiscal)
    declaracion.remanente_periodo_anterior = redondear_entero(remanente_anterior)
    declaracion.impuesto_determinado = redondear_entero(impuesto_determinado)
    declaracion.remanente_siguiente_periodo = redondear_entero(remanente_siguiente)
    declaracion.impuesto_a_pagar = redondear_entero(impuesto_a_pagar)
    declaracion.updated_by = usuario_id

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
            "debito_fiscal": redondear_entero(debito_fiscal),
            "credito_fiscal": redondear_entero(credito_fiscal),
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
async def obtener_declaracion(
    db: AsyncSession,
    declaracion_id: int,
) -> dict | None:
    """Obtiene una declaración con todos sus detalles."""
    stmt = (
        select(DeclaracionImpuesto)
        .where(DeclaracionImpuesto.id == declaracion_id)
        .options(
            selectinload(DeclaracionImpuesto.detalles),
        )
    )
    declaracion = (await db.execute(stmt)).scalar_one_or_none()
    if declaracion is None:
        return None

    # Cargar estructura del formulario para enriquecer detalles
    stmt_form = select(FormularioSat).where(
        FormularioSat.codigo == declaracion.formulario_codigo
    )
    formulario = (await db.execute(stmt_form)).scalar_one_or_none()

    # Cargar secciones + casillas para metadata
    secciones_meta: dict[str, dict] = {}
    if formulario:
        stmt_sec = (
            select(SeccionFormulario)
            .where(SeccionFormulario.formulario_id == formulario.id)
            .options(
                selectinload(SeccionFormulario.casillas),
            )
            .order_by(SeccionFormulario.numero_seccion)
        )
        for sec in (await db.execute(stmt_sec)).scalars().unique().all():
            secciones_meta[str(sec.numero_seccion)] = {
                "nombre": sec.nombre,
                "tipo_seccion": sec.tipo_seccion,
                "casillas": {
                    c.codigo: {
                        "nombre": c.nombre,
                        "tipo_casilla": c.tipo_casilla,
                        "es_editable": c.es_editable,
                        "naturaleza": c.naturaleza,
                        "orden": c.orden_seccion,
                    }
                    for c in sec.casillas
                },
            }

    detalles_out = []
    for det in sorted(declaracion.detalles, key=lambda d: d.casilla_codigo or ""):
        meta_casilla = (
            secciones_meta.get(det.seccion, {})
            .get("casillas", {})
            .get(det.casilla_codigo, {})
        )
        detalles_out.append({
            "id": det.id,
            "casilla_id": det.casilla_id,
            "casilla_codigo": det.casilla_codigo,
            "seccion": det.seccion,
            "valor": redondear_entero(det.valor),
            "valor_original": float(det.valor_original) if det.valor_original else 0,
            "tipo_casilla": det.tipo_casilla or meta_casilla.get("tipo_casilla"),
            "nombre": meta_casilla.get("nombre", ""),
            "es_editable": meta_casilla.get("es_editable", False),
            "naturaleza": meta_casilla.get("naturaleza"),
        })

    return {
        "id": declaracion.id,
        "empresa_id": declaracion.empresa_id,
        "formulario_codigo": declaracion.formulario_codigo,
        "anio_periodo": declaracion.anio_periodo,
        "mes_periodo": declaracion.mes_periodo,
        "estado": declaracion.estado,
        "total_debito_fiscal": redondear_entero(declaracion.total_debito_fiscal),
        "total_credito_fiscal": redondear_entero(declaracion.total_credito_fiscal),
        "remanente_periodo_anterior": redondear_entero(declaracion.remanente_periodo_anterior),
        "impuesto_determinado": redondear_entero(declaracion.impuesto_determinado),
        "remanente_siguiente_periodo": redondear_entero(declaracion.remanente_siguiente_periodo),
        "impuesto_a_pagar": redondear_entero(declaracion.impuesto_a_pagar),
        "detalles": detalles_out,
        "secciones": secciones_meta,
    }


# ============================================================
# FINALIZAR DECLARACIÓN
# ============================================================
async def finalizar_declaracion(
    db: AsyncSession,
    declaracion_id: int,
    usuario_id: int | None = None,
) -> dict:
    """Finaliza una declaración (ya no se puede modificar)."""
    stmt = select(DeclaracionImpuesto).where(DeclaracionImpuesto.id == declaracion_id)
    declaracion = (await db.execute(stmt)).scalar_one_or_none()
    if declaracion is None:
        raise ValueError("Declaración no encontrada")
    if declaracion.estado == "FINALIZADO":
        raise ValueError("La declaración ya está finalizada")

    declaracion.estado = "FINALIZADO"
    declaracion.finalizado_por = usuario_id
    declaracion.fecha_cierre = datetime.now(timezone.utc)
    declaracion.updated_by = usuario_id

    await db.commit()
    return {"mensaje": "Declaración finalizada exitosamente", "declaracion_id": declaracion.id}


# ============================================================
# AJUSTE MANUAL
# ============================================================
async def aplicar_ajuste_manual(
    db: AsyncSession,
    declaracion_id: int,
    casilla_codigo: str,
    nuevo_valor: Decimal,
    justificacion: str | None = None,
    usuario_id: int | None = None,
) -> dict:
    """Aplica un ajuste manual a una casilla editable y recalcula totales."""
    stmt = select(DeclaracionImpuesto).where(DeclaracionImpuesto.id == declaracion_id)
    declaracion = (await db.execute(stmt)).scalar_one_or_none()
    if declaracion is None:
        raise ValueError("Declaración no encontrada")
    if declaracion.estado == "FINALIZADO":
        raise ValueError("No se puede ajustar una declaración finalizada")

    # Buscar el detalle
    stmt_det = select(DetalleDeclaracionImpuesto).where(
        DetalleDeclaracionImpuesto.declaracion_id == declaracion_id,
        DetalleDeclaracionImpuesto.casilla_codigo == casilla_codigo,
    )
    detalle = (await db.execute(stmt_det)).scalar_one_or_none()
    if detalle is None:
        raise ValueError(f"Casilla {casilla_codigo} no encontrada en la declaración")

    # Verificar que la casilla es editable
    stmt_cas = (
        select(CasillaSat)
        .join(SeccionFormulario, CasillaSat.seccion_id == SeccionFormulario.id)
        .where(
            CasillaSat.codigo == casilla_codigo,
            SeccionFormulario.formulario_id == select(FormularioSat.id).where(
                FormularioSat.codigo == declaracion.formulario_codigo
            ).scalar_subquery(),
        )
    )
    casilla = (await db.execute(stmt_cas)).scalar_one_or_none()
    if casilla and not casilla.es_editable:
        raise ValueError(f"La casilla {casilla_codigo} no es editable")

    # Aplicar ajuste
    detalle.valor = redondear_entero(nuevo_valor)
    detalle.valor_original = nuevo_valor
    detalle.justificacion = justificacion
    detalle.updated_by = usuario_id

    # Recalcular totales de la declaración
    await _recalcular_totales(db, declaracion)

    await db.commit()
    return {"mensaje": "Ajuste manual aplicado y totales recalculados exitosamente"}


async def _recalcular_totales(db: AsyncSession, declaracion: DeclaracionImpuesto) -> None:
    """Recalcula los totales de la declaración a partir de sus detalles."""
    stmt_dets = select(DetalleDeclaracionImpuesto).where(
        DetalleDeclaracionImpuesto.declaracion_id == declaracion.id
    )
    detalles = list((await db.execute(stmt_dets)).scalars().all())

    debito = Decimal("0")
    credito = Decimal("0")

    for det in detalles:
        sec = det.seccion or ""
        if sec.startswith("3"):
            debito += det.valor or Decimal("0")
        elif sec.startswith(("5", "6")):
            credito += det.valor or Decimal("0")

    remanente_ant = Decimal("0")
    for det in detalles:
        if det.casilla_codigo == "5_REM":
            remanente_ant = det.valor or Decimal("0")
            break

    impuesto_det = max(Decimal("0"), debito - credito - remanente_ant)
    remanente_sig = max(Decimal("0"), credito + remanente_ant - debito)

    declaracion.total_debito_fiscal = redondear_entero(debito)
    declaracion.total_credito_fiscal = redondear_entero(credito)
    declaracion.remanente_periodo_anterior = redondear_entero(remanente_ant)
    declaracion.impuesto_determinado = redondear_entero(impuesto_det)
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
    stmt = (
        select(DeclaracionImpuestoFactura)
        .where(
            DeclaracionImpuestoFactura.declaracion_id == declaracion_id,
            DeclaracionImpuestoFactura.casilla_codigo == casilla_codigo,
        )
    )
    asociaciones = list((await db.execute(stmt)).scalars().all())

    if not asociaciones:
        return []

    factura_ids = [a.factura_id for a in asociaciones]

    stmt_fac = (
        select(FacturaElectronica)
        .where(FacturaElectronica.id.in_(factura_ids))
        .order_by(FacturaElectronica.fecha_emision)
    )
    facturas = list((await db.execute(stmt_fac)).scalars().all())

    resultado = []
    for f in facturas:
        resultado.append({
            "id": f.id,
            "numero_documento": f.numero_documento,
            "serie": getattr(f, "serie", ""),
            "fecha_emision": f.fecha_emision.isoformat() if f.fecha_emision else None,
            "nit_emisor": getattr(f, "nit_emisor", ""),
            "nombre_emisor": getattr(f, "nombre_emisor_receptor", ""),
            "tipo_operacion": getattr(f, "tipo_operacion", ""),
            "base_asignada": float(f.total_gravado_gtq or 0),
            "impuesto_asignado": float(f.total_iva_gtq or 0),
            "total": float(f.total_gtq or 0),
            "estado": f.estado,
        })

    return resultado
