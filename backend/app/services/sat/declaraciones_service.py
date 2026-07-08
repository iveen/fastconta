# app/services/declaraciones_service.py
import logging
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, Union

from app.models.global_models import CasillaSat, FormularioSat
from app.models.tenant_models import (
    DeclaracionImpuesto,
    DeclaracionImpuestoFactura,
    DetalleDeclaracionImpuesto,
    FacturaElectronica,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

PAISES_CENTROAMERICA = [
    'GUATEMALA', 'BELICE', 'EL SALVADOR', 'HONDURAS',
    'NICARAGUA', 'COSTA RICA', 'PANAMA',
]


def clasificar_destino_exportacion(pais: str) -> str:
    if not pais:
        return 'DESCONOCIDO'
    pais_upper = pais.upper().strip()
    if pais_upper in PAISES_CENTROAMERICA:
        return 'CENTROAMERICA'
    return 'RESTO_MUNDO'


def redondear_entero(valor: Union[Decimal, float, int, None]) -> int:
    """Redondea a entero (0 decimales) de forma segura."""
    if valor is None:
        return 0
    if isinstance(valor, int):
        return valor
    if not isinstance(valor, Decimal):
        valor = Decimal(str(valor))
    return int(valor.quantize(Decimal('1'), rounding=ROUND_HALF_UP))


# ============================================================
# MOTOR DE MAPEO SAT-2237
# ============================================================
MAPA_CALCULO_SAT_2237 = {
    # --- SECCIÓN 3: DÉBITO FISCAL ---
    "VENTAS_GRAVADAS_LOCALES": {
        "tipo": "DEBITO",
        "seccion": "3",
        "filtro": lambda f: f.tipo_operacion == "Venta" and not f.es_exportacion and f.total_gravado > 0,
        "campo_base": "total_gravado_gtq",
        "campo_impuesto": "total_iva_gtq",
    },
    "SERVICIOS_GRAVADOS_LOCALES": {
        "tipo": "DEBITO",
        "seccion": "3",
        "filtro": lambda f: f.tipo_operacion == "Venta" and not f.es_exportacion and f.total_gravado_servicios_gtq > 0,
        "campo_base": "total_gravado_servicios_gtq",
        "campo_impuesto": "total_iva_servicios_gtq",
    },
    # --- SECCIÓN 4: EXPORTACIONES (REFERENCIA) ---
    "EXPORTACIONES_CENTROAMERICA": {
        "tipo": "EXPORTACION",
        "seccion": "4",
        "filtro": lambda f: f.es_exportacion and clasificar_destino_exportacion(f.pais_destino_exportacion or '') == 'CENTROAMERICA',
        "campo_base": "total_gtq",
        "campo_impuesto": None,
    },
    "EXPORTACIONES_RESTO_MUNDO": {
        "tipo": "EXPORTACION",
        "seccion": "4",
        "filtro": lambda f: f.es_exportacion and clasificar_destino_exportacion(f.pais_destino_exportacion or '') == 'RESTO_MUNDO',
        "campo_base": "total_gtq",
        "campo_impuesto": None,
    },
    # --- SECCIÓN 5: CRÉDITO FISCAL LOCAL ---
    "COMPRAS_COMBUSTIBLES_LOCALES": {
        "tipo": "CREDITO",
        "seccion": "5",
        "filtro": lambda f: f.tipo_operacion == "Compra" and getattr(f, 'clasificacion_gasto_sat', 'NORMAL') == 'COMBUSTIBLE',
        "campo_base": "total_gravado_gtq",
        "campo_impuesto": "total_iva_gtq",
    },
    "COMPRAS_ACTIVO_FIJO_LOCALES": {
        "tipo": "CREDITO",
        "seccion": "5",
        "filtro": lambda f: f.tipo_operacion == "Compra" and getattr(f, 'clasificacion_gasto_sat', 'NORMAL') == 'ACTIVO_FIJO',
        "campo_base": "total_gravado_gtq",
        "campo_impuesto": "total_iva_gtq",
    },
    "COMPRAS_PEQUENO_CONTRIBUYENTE": {
        "tipo": "CREDITO",
        "seccion": "5",
        "filtro": lambda f: f.tipo_operacion == "Compra" and getattr(f, 'clasificacion_gasto_sat', 'NORMAL') == 'PEQUENO_CONTRIBUYENTE',
        "campo_base": "total_gravado_gtq",
        "campo_impuesto": "total_iva_gtq",
    },
    "OTRAS_COMPRAS_LOCALES": {
        "tipo": "CREDITO",
        "seccion": "5",
        "filtro": lambda f: f.tipo_operacion == "Compra" and getattr(f, 'clasificacion_gasto_sat', 'NORMAL') in ['NORMAL', 'MEDICAMENTO'],
        "campo_base": "total_gravado_gtq",
        "campo_impuesto": "total_iva_gtq",
    },
    # --- SECCIÓN 6: CRÉDITO FISCAL EXPORTACIONES ---
    "REMANENTE_CREDITO_EXPORTACIONES": {
        "tipo": "CREDITO",
        "seccion": "6",
        "filtro": lambda f: False,
        "campo_base": None,
        "campo_impuesto": None,
    },
    # --- SECCIÓN 7: DETERMINACIÓN DEL IMPUESTO ---
    "RETENCIONES_IVA_RECIBIDAS": {
        "tipo": "RETENCION",
        "seccion": "7",
        "filtro": lambda f: f.tipo_operacion == "Compra" and getattr(f, 'retencion_iva', 0) > 0,
        "campo_base": None,
        "campo_impuesto": "retencion_iva",
    },
    "IMPUESTO_TOTAL_DETERMINADO_LOCAL": {
        "tipo": "CALCULADO",
        "seccion": "7",
        "filtro": None,
        "campo_base": None,
        "campo_impuesto": None,
    },
    "CREDITO_FISCAL_PERIODO_SIGUIENTE_LOCAL": {
        "tipo": "CALCULADO",
        "seccion": "7",
        "filtro": None,
        "campo_base": None,
        "campo_impuesto": None,
    },
    "IMPUESTO_A_PAGAR": {
        "tipo": "CALCULADO",
        "seccion": "7",
        "filtro": None,
        "campo_base": None,
        "campo_impuesto": None,
    },
    # --- SECCIÓN 8: INDICADORES COMERCIALES ---
    "INDICADORES_COMERCIALES": {
        "tipo": "INDICADOR",
        "seccion": "8",
        "filtro": None,
        "campo_base": None,
        "campo_impuesto": None,
    },
    "RAZON_VENTAS_COMPRAS": {
        "tipo": "INDICADOR",
        "seccion": "8",
        "filtro": None,
        "campo_base": None,
        "campo_impuesto": None,
    },
    # --- SECCIÓN 9.1: CANTIDAD DE OPERACIONES ---
    "INDICADOR_CANTIDAD_FACTURAS_EMITIDAS": {
        "tipo": "INDICADOR",
        "seccion": "9.1",
        "filtro": lambda f: f.tipo_operacion == "Venta",
        "campo_base": None,
        "campo_impuesto": None,
    },
    "INDICADOR_CANTIDAD_FACTURAS_RECIBIDAS": {
        "tipo": "INDICADOR",
        "seccion": "9.1",
        "filtro": lambda f: f.tipo_operacion == "Compra",
        "campo_base": None,
        "campo_impuesto": None,
    },
    # --- SECCIÓN 9.2: MONTO DE OPERACIONES ---
    "INDICADOR_MONTO_NC_EMITIDAS": {
        "tipo": "INDICADOR",
        "seccion": "9.2",
        "filtro": lambda f: f.tipo_documento in ["NCRE", "NC"] and f.tipo_operacion == "Venta",
        "campo_base": "total_gtq",
        "campo_impuesto": None,
    },
    "INDICADOR_MONTO_ND_EMITIDAS": {
        "tipo": "INDICADOR",
        "seccion": "9.2",
        "filtro": lambda f: f.tipo_documento in ["NDEB", "ND"] and f.tipo_operacion == "Venta",
        "campo_base": "total_gtq",
        "campo_impuesto": None,
    },
}


# ============================================================
# SERVICIO PRINCIPAL
# ============================================================
async def generar_formulario_sombra(
    db: AsyncSession,
    empresa_id: int,  # ✅ BIGINT (era UUID)
    anio: int,
    mes: int,
    codigo_formulario: str = "SAT-2237"
) -> Dict[str, Any]:
    # 1. Obtener formulario y casillas
    stmt_form = select(FormularioSat).where(FormularioSat.codigo == codigo_formulario)
    res_form = await db.execute(stmt_form)
    formulario = res_form.scalar_one_or_none()
    if not formulario:
        raise ValueError(f"Formulario {codigo_formulario} no encontrado")

    stmt_casillas = select(CasillaSat).where(
        CasillaSat.formulario_id == formulario.id
    ).order_by(CasillaSat.seccion, CasillaSat.orden_seccion)
    res_casillas = await db.execute(stmt_casillas)
    casillas = res_casillas.scalars().all()

    # 2. Obtener o crear declaración
    stmt_decl = select(DeclaracionImpuesto).where(
        DeclaracionImpuesto.empresa_id == empresa_id,
        DeclaracionImpuesto.formulario_sat_id == formulario.id,
        DeclaracionImpuesto.anio == anio,
        DeclaracionImpuesto.mes == mes
    )
    res_decl = await db.execute(stmt_decl)
    declaracion = res_decl.scalar_one_or_none()
    if not declaracion:
        remanente_anterior = Decimal("0.00")
        mes_ant = mes - 1 if mes > 1 else 12
        anio_ant = anio if mes > 1 else anio - 1
        stmt_remanente = select(DeclaracionImpuesto.remanente_siguiente_periodo).where(
            DeclaracionImpuesto.empresa_id == empresa_id,
            DeclaracionImpuesto.formulario_sat_id == formulario.id,
            DeclaracionImpuesto.anio == anio_ant,
            DeclaracionImpuesto.mes == mes_ant,
            DeclaracionImpuesto.estado == "FINALIZADO"
        )
        res_remanente = await db.execute(stmt_remanente)
        remanente_val = res_remanente.scalar_one_or_none()
        if remanente_val:
            remanente_anterior = remanente_val
        declaracion = DeclaracionImpuesto(
            empresa_id=empresa_id,
            formulario_sat_id=formulario.id,
            anio=anio,
            mes=mes,
            estado="BORRADOR",
            remanente_periodo_anterior=remanente_anterior
        )
        db.add(declaracion)
        await db.flush()

    # 3. Obtener facturas (EXCLUYENDO anuladas para cálculo)
    from sqlalchemy.orm import selectinload
    stmt_facturas = select(FacturaElectronica).where(
        FacturaElectronica.empresa_id == empresa_id,
        func.extract('year', FacturaElectronica.fecha_emision) == anio,
        func.extract('month', FacturaElectronica.fecha_emision) == mes,
        FacturaElectronica.estado != "Anulada",
        FacturaElectronica.tipo_operacion.in_(["Venta", "Compra"])
    ).options(selectinload(FacturaElectronica.detalles))
    res_facturas = await db.execute(stmt_facturas)
    facturas = res_facturas.scalars().all()

    # 3b. TODAS las facturas (INCLUYENDO anuladas) para indicadores
    stmt_todas = select(FacturaElectronica).where(
        FacturaElectronica.empresa_id == empresa_id,
        func.extract('year', FacturaElectronica.fecha_emision) == anio,
        func.extract('month', FacturaElectronica.fecha_emision) == mes,
        FacturaElectronica.tipo_operacion.in_(["Venta", "Compra"])
    )
    res_todas = await db.execute(stmt_todas)
    todas_las_facturas = res_todas.scalars().all()

    # 4. Procesar casillas
    total_debito = Decimal("0.00")
    total_credito = Decimal("0.00")
    total_retenciones = Decimal("0.00")
    total_exportaciones = Decimal("0.00")
    total_base_debitos = Decimal("0.00")
    total_base_creditos = Decimal("0.00")

    for casilla in casillas:
        regla = MAPA_CALCULO_SAT_2237.get(casilla.codigo)
        base_calc = Decimal("0.00")
        imp_calc = Decimal("0.00")
        facturas_asociadas_ids = []

        if regla:
            facturas_a_procesar = todas_las_facturas if regla["tipo"] == "INDICADOR" else facturas
            filtro = regla.get("filtro")
            if filtro is not None:
                for f in facturas_a_procesar:
                    try:
                        if filtro(f):
                            facturas_asociadas_ids.append(f.id)
                            if regla["campo_base"] and hasattr(f, regla["campo_base"]):
                                base_calc += getattr(f, regla["campo_base"]) or Decimal("0.00")
                            if regla["campo_impuesto"] and hasattr(f, regla["campo_impuesto"]):
                                imp_calc += getattr(f, regla["campo_impuesto"]) or Decimal("0.00")
                    except Exception as e:
                        logger.error(f"Error aplicando filtro {casilla.codigo}: {e}")
                        continue

            if regla["tipo"] == "INDICADOR":
                imp_calc = Decimal(len(facturas_asociadas_ids))
                base_calc = Decimal("0.00")

            if regla["tipo"] == "DEBITO":
                total_debito += imp_calc
                total_base_debitos += base_calc
            elif regla["tipo"] == "CREDITO":
                total_credito += imp_calc
                total_base_creditos += base_calc
            elif regla["tipo"] == "EXPORTACION":
                total_exportaciones += base_calc
                total_base_debitos += base_calc
            elif regla["tipo"] == "RETENCION":
                total_retenciones += imp_calc
        else:
            logger.warning(f"⚠️ Casilla {casilla.codigo} no tiene regla")

        # 5. Guardar detalle (REDONDEADO A ENTEROS)
        stmt_detalle = select(DetalleDeclaracionImpuesto).where(
            DetalleDeclaracionImpuesto.declaracion_id == declaracion.id,
            DetalleDeclaracionImpuesto.casilla_sat_id == casilla.id
        )
        res_detalle = await db.execute(stmt_detalle)
        detalle = res_detalle.scalar_one_or_none()

        base_redondeada = redondear_entero(base_calc)
        imp_redondeado = redondear_entero(imp_calc)

        if not detalle:
            detalle = DetalleDeclaracionImpuesto(
                declaracion_id=declaracion.id,
                casilla_sat_id=casilla.id,
                base_imponible=base_redondeada,
                monto_impuesto=imp_redondeado,
                es_ajuste_manual=False
            )
            db.add(detalle)
            await db.flush()
        else:
            if not detalle.es_ajuste_manual:
                detalle.base_imponible = base_redondeada
                detalle.monto_impuesto = imp_redondeado

        # 6. Drill-down
        await db.execute(
            DeclaracionImpuestoFactura.__table__.delete().where(
                DeclaracionImpuestoFactura.detalle_declaracion_id == detalle.id
            )
        )
        for fid in facturas_asociadas_ids:
            f_obj = next((f for f in facturas_a_procesar if f.id == fid), None)
            base_asig = (getattr(f_obj, regla["campo_base"], 0) or 0) if regla and regla.get("campo_base") else 0
            imp_asig = (getattr(f_obj, regla["campo_impuesto"], 0) or 0) if regla and regla.get("campo_impuesto") else 0
            if regla and regla["tipo"] == "INDICADOR":
                base_asig = 0
                imp_asig = 1
            db.add(DeclaracionImpuestoFactura(
                detalle_declaracion_id=detalle.id,
                factura_id=fid,
                base_asignada=base_asig,
                impuesto_asignado=imp_asig
            ))

    # 7. CÁLCULO SECCIÓN 7
    impuesto_determinado = total_debito - total_credito
    remanente_anterior = declaracion.remanente_periodo_anterior or Decimal("0.00")
    if impuesto_determinado > 0:
        impuesto_a_pagar = impuesto_determinado - total_retenciones
        if impuesto_a_pagar > 0:
            credito_fiscal_siguiente = Decimal("0.00")
        else:
            credito_fiscal_siguiente = abs(impuesto_a_pagar)
            impuesto_a_pagar = Decimal("0.00")
    else:
        impuesto_a_pagar = Decimal("0.00")
        credito_fiscal_siguiente = abs(impuesto_determinado) + remanente_anterior

    # 8. CÁLCULO DE SECCIÓN 8: INDICADORES COMERCIALES
    indicadores_comerciales = total_base_debitos - total_base_creditos
    razon_ventas_compras = Decimal("0.00")
    if total_base_creditos > 0:
        razon_ventas_compras = total_base_debitos / total_base_creditos

    casillas_seccion8 = {
        "INDICADORES_COMERCIALES": redondear_entero(indicadores_comerciales),
        "RAZON_VENTAS_COMPRAS": int(razon_ventas_compras * 100),
    }
    for codigo_casilla, valor in casillas_seccion8.items():
        stmt_casilla = select(CasillaSat).where(
            CasillaSat.codigo == codigo_casilla,
            CasillaSat.formulario_id == formulario.id
        )
        res_casilla = await db.execute(stmt_casilla)
        casilla_8 = res_casilla.scalar_one_or_none()
        if casilla_8:
            stmt_detalle_8 = select(DetalleDeclaracionImpuesto).where(
                DetalleDeclaracionImpuesto.declaracion_id == declaracion.id,
                DetalleDeclaracionImpuesto.casilla_sat_id == casilla_8.id
            )
            res_detalle_8 = await db.execute(stmt_detalle_8)
            detalle_8 = res_detalle_8.scalar_one_or_none()
            if not detalle_8:
                detalle_8 = DetalleDeclaracionImpuesto(
                    declaracion_id=declaracion.id,
                    casilla_sat_id=casilla_8.id,
                    base_imponible=0,
                    monto_impuesto=valor,
                    es_ajuste_manual=False
                )
                db.add(detalle_8)

    # 9. Actualizar cabecera (REDONDEADO)
    declaracion.total_debito_fiscal = redondear_entero(total_debito)
    declaracion.total_credito_fiscal = redondear_entero(total_credito)
    declaracion.impuesto_determinado = redondear_entero(impuesto_determinado)
    declaracion.impuesto_a_pagar = redondear_entero(max(Decimal("0.00"), impuesto_a_pagar))
    declaracion.remanente_siguiente_periodo = redondear_entero(credito_fiscal_siguiente)

    # 10. Actualizar casillas CALCULADO de Sección 7
    casillas_calculado = {
        "IMPUESTO_TOTAL_DETERMINADO_LOCAL": redondear_entero(max(Decimal("0.00"), impuesto_determinado)),
        "CREDITO_FISCAL_PERIODO_SIGUIENTE_LOCAL": redondear_entero(credito_fiscal_siguiente),
        "IMPUESTO_A_PAGAR": redondear_entero(max(Decimal("0.00"), impuesto_a_pagar)),
    }
    for codigo_casilla, valor in casillas_calculado.items():
        stmt_casilla = select(CasillaSat).where(
            CasillaSat.codigo == codigo_casilla,
            CasillaSat.formulario_id == formulario.id
        )
        res_casilla = await db.execute(stmt_casilla)
        casilla_calc = res_casilla.scalar_one_or_none()
        if casilla_calc:
            stmt_detalle_calc = select(DetalleDeclaracionImpuesto).where(
                DetalleDeclaracionImpuesto.declaracion_id == declaracion.id,
                DetalleDeclaracionImpuesto.casilla_sat_id == casilla_calc.id
            )
            res_detalle_calc = await db.execute(stmt_detalle_calc)
            detalle_calc = res_detalle_calc.scalar_one_or_none()
            if not detalle_calc:
                detalle_calc = DetalleDeclaracionImpuesto(
                    declaracion_id=declaracion.id,
                    casilla_sat_id=casilla_calc.id,
                    base_imponible=0,
                    monto_impuesto=valor,
                    es_ajuste_manual=False
                )
                db.add(detalle_calc)
            else:
                if not detalle_calc.es_ajuste_manual:
                    detalle_calc.monto_impuesto = valor

    await db.flush()
    await db.commit()

    logger.info(f"""
    ========================================
    RESUMEN DECLARACIÓN {declaracion.id}
    ========================================
    Débito Fiscal: {declaracion.total_debito_fiscal}
    Crédito Fiscal: {declaracion.total_credito_fiscal}
    Impuesto Determinado: {declaracion.impuesto_determinado}
    Crédito Fiscal Sig. Período: {declaracion.remanente_siguiente_periodo}
    Impuesto a Pagar: {declaracion.impuesto_a_pagar}
    Total Exportaciones: {redondear_entero(total_exportaciones)}
    ========================================
    """)

    return {
        "mensaje": "Formulario sombra generado exitosamente",
        "declaracion_id": declaracion.id,  # ✅ CORREGIDO: int (no str)
        "estado": declaracion.estado,
        "totales": {
            "debito_fiscal": redondear_entero(declaracion.total_debito_fiscal),
            "credito_fiscal": redondear_entero(declaracion.total_credito_fiscal),
            "remanente_anterior": redondear_entero(declaracion.remanente_periodo_anterior),
            "impuesto_a_pagar": redondear_entero(declaracion.impuesto_a_pagar),
            "remanente_siguiente": redondear_entero(declaracion.remanente_siguiente_periodo),
            "exportaciones": redondear_entero(total_exportaciones),
        }
    }