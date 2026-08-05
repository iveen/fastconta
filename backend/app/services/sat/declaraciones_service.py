"""
Servicio de Declaraciones de Impuestos – Motor Genérico con Strategy Pattern

Este servicio maneja la lógica común para todos los formularios SAT:
- Carga de estructura (formulario, secciones, casillas)
- Carga de facturas del período
- Motor de cálculo con reglas de filtrado
- Evaluación de fórmulas con resolución de dependencias
- Persistencia de declaraciones

La lógica específica de cada formulario se delega a estrategias registradas
en app/services/sat/strategies/
"""

import logging
from decimal import Decimal
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
from app.services.sat.evaluators import FormulaEvaluator
from app.services.sat.strategies import obtener_estrategia

logger = logging.getLogger(__name__)


# ============================================================
# HELPERS
# ============================================================
def redondear_entero(valor: Decimal | float | int | None) -> int:
    """Redondea a entero (el formulario SAT usa Q enteros)."""
    if valor is None:
        return 0
    try:
        from decimal import ROUND_HALF_UP, InvalidOperation
        return int(Decimal(str(valor)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except (InvalidOperation, ValueError):
        return 0


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
        valor = getattr(factura, campo, None)

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
                    if campo:
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
# CARGA DE ESTRUCTURA
# ============================================================
async def _cargar_formulario(db: AsyncSession, codigo_formulario: str) -> tuple[FormularioSat, list[SeccionFormulario], list[CasillaSat]]:
    """Carga el formulario con secciones y casillas."""
    stmt_form = select(FormularioSat).where(
        FormularioSat.codigo == codigo_formulario,
        FormularioSat.es_version_activa.is_(True),
    )
    formulario = (await db.execute(stmt_form)).scalar_one_or_none()
    if formulario is None:
        raise ValueError(f"Formulario {codigo_formulario} no encontrado en BD. Ejecutar seed.")

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

    # Aplanar casillas
    todas_casillas: list[CasillaSat] = []
    for sec in secciones:
        for cas in sorted(sec.casillas, key=lambda c: c.orden_seccion or 0):
            todas_casillas.append(cas)

    logger.info(f"{codigo_formulario}: {len(secciones)} secciones, {len(todas_casillas)} casillas cargadas")
    return formulario, secciones, todas_casillas


# ============================================================
# CARGA DE FACTURAS
# ============================================================
async def _cargar_facturas(db: AsyncSession, empresa_id: int, anio: int, mes: int) -> list[FacturaElectronica]:
    """Carga las facturas FEL del período."""
    from datetime import date
    
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
    facturas = list((await db.execute(stmt_facturas)).scalars().all())
    logger.info(f"{empresa_id}: {len(facturas)} facturas para período {anio}-{mes:02d}")
    return facturas


# ============================================================
# EVALUACIÓN DE FÓRMULAS
# ============================================================
def _evaluar_formulas(
    todas_casillas: list[CasillaSat],
    valores: dict[str, Decimal],
) -> dict[str, Decimal]:
    """Evalúa fórmulas con resolución iterativa de dependencias."""
    casillas_con_formula = [
        c for c in todas_casillas
        if c.formula_calculo and c.codigo not in valores
    ]

    max_iteraciones = 20
    for _iter in range(max_iteraciones):
        calculadas_en_iter = 0
        for casilla in list(casillas_con_formula):
            # Verificar que todas las dependencias estén resueltas
            dependencias = FormulaEvaluator.extraer_dependencias(casilla.formula_calculo)
            if all(dep in valores for dep in dependencias):
                valores[casilla.codigo] = FormulaEvaluator.evaluar(casilla.formula_calculo, valores)
                casillas_con_formula.remove(casilla)
                calculadas_en_iter += 1

        if not casillas_con_formula:
            break
        if calculadas_en_iter == 0:
            codigos_pendientes = [c.codigo for c in casillas_con_formula]
            logger.warning(f"No se pudieron resolver fórmulas (iter {_iter}): {codigos_pendientes}")
            for c in casillas_con_formula:
                valores[c.codigo] = Decimal("0")
            break

    logger.info(f"Fórmulas resueltas en {_iter + 1} iteración(es)")
    return valores


# ============================================================
# FUNCIÓN PRINCIPAL: GENERAR FORMULARIO SOMBRA
# ============================================================
async def generar_formulario_sombra(
    db: AsyncSession,
    empresa_id: int,
    anio: int,
    mes: int,
    codigo_formulario: str = "SAT-2237",
    usuario_id: int | None = None,
) -> dict[str, Any]:
    """
    Genera (o regenera) la declaración sombra para un formulario y período.
    
    Flujo:
      1. Obtener estrategia específica del formulario
      2. Cargar estructura (formulario, secciones, casillas)
      3. Cargar facturas del período
      4. Preparar contexto específico (delegado a estrategia)
      5. Calcular casillas con reglas de filtrado
      6. Evaluar fórmulas con resolución de dependencias
      7. Calcular totales de cabecera (delegado a estrategia)
      8. Persistir declaración + detalles + asociaciones
    """

    # ================================================================
    # PASO 1: Obtener estrategia específica
    # ================================================================
    estrategia = obtener_estrategia(codigo_formulario)
    logger.info(f"Iniciando generación de {codigo_formulario} para empresa {empresa_id}, período {anio}-{mes:02d}")

    # ================================================================
    # PASO 2: Cargar estructura
    # ================================================================
    formulario, secciones, todas_casillas = await _cargar_formulario(db, codigo_formulario)

    # ================================================================
    # PASO 3: Cargar facturas
    # ================================================================
    facturas = await _cargar_facturas(db, empresa_id, anio, mes)

    # ================================================================
    # PASO 4: Preparar contexto específico (delegado a estrategia)
    # ================================================================
    contexto = await estrategia.preparar_contexto(db, empresa_id, anio, mes)

    # ================================================================
    # PASO 5: Verificar / crear declaración
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
            raise ValueError(f"La declaración de {anio}-{mes:02d} ya está finalizada. No se puede regenerar.")
        # Limpiar detalles y asociaciones previas
        stmt_del_det = select(DetalleDeclaracionImpuesto).where(
            DetalleDeclaracionImpuesto.declaracion_id == declaracion.id
        )
        for det in (await db.execute(stmt_del_det)).scalars().all():
            await db.delete(det)
        await db.flush()
        declaracion.estado = "BORRADOR"
    else:
        declaracion = DeclaracionImpuesto(
            empresa_id=empresa_id,
            formulario_sat_id=formulario.id,
            anio=anio,
            mes=mes,
            estado="BORRADOR",
            remanente_periodo_anterior=contexto.get("remanente_anterior", Decimal("0")),
        )
        db.add(declaracion)
        await db.flush()

    # ================================================================
    # PASO 6: Calcular casillas con reglas de filtrado
    # ================================================================
    valores: dict[str, Decimal] = {}
    facturas_por_casilla: dict[str, list[int]] = {}

    for casilla in todas_casillas:
        reglas_activas = [r for r in (casilla.reglas_filtrado or []) if getattr(r, "es_activa", True)]
        if not reglas_activas:
            continue

        base, impuesto, fac_ids = calcular_casilla_con_reglas(
            facturas=facturas,
            reglas=reglas_activas,
            exclusiones=casilla.exclusiones or [],
        )

        valores[casilla.codigo] = base
        facturas_por_casilla[casilla.codigo] = fac_ids

    logger.info(f"{codigo_formulario}: {len(valores)} casillas calculadas con reglas de filtrado")

    # ================================================================
    # PASO 7: Evaluar fórmulas
    # ================================================================
    valores = _evaluar_formulas(todas_casillas, valores)

    # Inicializar casillas sin valor en 0
    for casilla in todas_casillas:
        if casilla.codigo not in valores:
            valores[casilla.codigo] = Decimal("0")

    # ================================================================
    # PASO 8: Calcular totales de cabecera (delegado a estrategia)
    # ================================================================
    totales = estrategia.calcular_totales_cabecera(valores, contexto)

    # ================================================================
    # PASO 9: Persistir detalles y asociaciones
    # ================================================================
    for casilla in todas_casillas:
        valor_raw = valores.get(casilla.codigo, Decimal("0"))
        
        # Clasificar valor según tipo_casilla (delegado a estrategia)
        base_val, imp_val = estrategia.clasificar_valor_casilla(casilla.tipo_casilla, valor_raw)

        detalle = DetalleDeclaracionImpuesto(
            declaracion_id=declaracion.id,
            casilla_sat_id=casilla.id,
            base_imponible=redondear_entero(base_val),
            monto_impuesto=redondear_entero(imp_val),
            es_ajuste_manual=False,
        )
        db.add(detalle)
        await db.flush()

        # Asociaciones de facturas
        fac_ids = facturas_por_casilla.get(casilla.codigo, [])
        for fid in fac_ids:
            factura_obj = next((f for f in facturas if f.id == fid), None)
            base_asig = Decimal("0")
            imp_asig = Decimal("0")
            
            if factura_obj:
                for regla in (casilla.reglas_filtrado or []):
                    if not getattr(regla, "es_activa", True):
                        continue
                    if factura_cumple_criterios(factura_obj, regla.criterios_json or {}):
                        campo = regla.campo_factura
                        if campo:
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
    # PASO 10: Actualizar totales en cabecera
    # ================================================================
    declaracion.total_debito_fiscal = totales["total_debito_fiscal"]
    declaracion.total_credito_fiscal = totales["total_credito_fiscal"]
    declaracion.remanente_periodo_anterior = totales["remanente_periodo_anterior"]
    declaracion.impuesto_determinado = totales["impuesto_determinado"]
    declaracion.remanente_siguiente_periodo = totales["remanente_siguiente_periodo"]
    declaracion.impuesto_a_pagar = totales["impuesto_a_pagar"]

    # Hook opcional para lógica adicional (delegado a estrategia)
    estrategia.aplicar_logica_post_calculo(db, declaracion, valores, contexto)

    await db.commit()

    logger.info(
        f"{codigo_formulario}: Declaración {declaracion.id} generada → "
        f"Débito={declaracion.total_debito_fiscal}, "
        f"Crédito={declaracion.total_credito_fiscal}, "
        f"Impuesto={declaracion.impuesto_a_pagar}"
    )

    return {
        "mensaje": "Formulario sombra generado exitosamente",
        "declaracion_id": declaracion.id,
        "estado": declaracion.estado,
        "totales": {
            "debito_fiscal": int(declaracion.total_debito_fiscal),
            "credito_fiscal": int(declaracion.total_credito_fiscal),
            "remanente_anterior": int(declaracion.remanente_periodo_anterior),
            "impuesto_determinado": int(declaracion.impuesto_determinado),
            "impuesto_a_pagar": int(declaracion.impuesto_a_pagar),
            "remanente_siguiente": int(declaracion.remanente_siguiente_periodo),
        },
        "casillas_calculadas": len(valores),
        "facturas_procesadas": len(facturas),
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
            "seccion": str(casilla.seccion_rel.numero_seccion) if casilla and casilla.seccion_rel else "",
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
    """Finaliza una declaración (ya no se puede modificar)."""
    from datetime import datetime, timezone
    
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

        if det.casilla and det.casilla.codigo == "5_REM":
            remanente_ant = det.monto_impuesto or Decimal("0")

    # Obtener estrategia para calcular totales
    stmt_form = select(FormularioSat.codigo).where(
        FormularioSat.id == declaracion.formulario_sat_id
    )
    form_codigo = (await db.execute(stmt_form)).scalar_one_or_none()
    
    if form_codigo:
        estrategia = obtener_estrategia(form_codigo)
        valores = {det.casilla.codigo: det.monto_impuesto or Decimal("0") for det, _ in rows if det.casilla}
        contexto = {"remanente_anterior": remanente_ant}
        totales = estrategia.calcular_totales_cabecera(valores, contexto)
        
        declaracion.total_debito_fiscal = totales["total_debito_fiscal"]
        declaracion.total_credito_fiscal = totales["total_credito_fiscal"]
        declaracion.impuesto_determinado = totales["impuesto_determinado"]
        declaracion.remanente_periodo_anterior = totales["remanente_periodo_anterior"]
        declaracion.remanente_siguiente_periodo = totales["remanente_siguiente_periodo"]
        declaracion.impuesto_a_pagar = totales["impuesto_a_pagar"]


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
