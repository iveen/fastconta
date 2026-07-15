"""
Estructura de datos del Formulario SAT-2237 (IVA General)
Versión 2.0 (Activa 2026): Incluye secciones 9.1 y 9.2 separadas.
Basado en el formulario oficial SAT-2237 Release 2.
"""

FORMULARIO_SAT_2237 = {
    "codigo": "SAT-2237",
    "version": "2.0",
    "nombre": "Declaración Jurativa Mensual del IVA - Régimen General",
    "descripcion": "IVA GENERAL SAT-2237 Release 2. Contribuyentes que realizan operaciones locales, de exportación y/o transferencia. Incluye secciones 9.1 y 9.2 separadas.",
    "es_version_activa": True,
    "editable": True,
}

SECCIONES_SAT_2237 = [
    {"numero_seccion": "1", "titulo": "NIT DEL CONTRIBUYENTE", "tipo_seccion": "IDENTIFICACION", "orden": 1, "es_obligatoria": True},
    {"numero_seccion": "2", "titulo": "PERÍODO DE IMPOSICIÓN", "tipo_seccion": "PERIODO", "orden": 2, "es_obligatoria": True},
    {"numero_seccion": "3", "titulo": "DÉBITO FISCAL POR OPERACIONES LOCALES", "tipo_seccion": "DEBITO_FISCAL", "orden": 3, "es_obligatoria": True},
    {"numero_seccion": "4", "titulo": "OPERACIONES DE EXPORTACIÓN Y TRANSFERENCIA", "tipo_seccion": "EXPORTACIONES", "orden": 4, "es_obligatoria": True},
    {"numero_seccion": "5", "titulo": "CRÉDITO FISCAL POR OPERACIONES LOCALES", "tipo_seccion": "CREDITO_FISCAL", "orden": 5, "es_obligatoria": True},
    {"numero_seccion": "6", "titulo": "CRÉDITO FISCAL EXPORTACIONES", "tipo_seccion": "CREDITO_FISCAL", "orden": 6, "es_obligatoria": True},
    {"numero_seccion": "7", "titulo": "DETERMINACIÓN", "tipo_seccion": "DETERMINACION", "orden": 7, "es_obligatoria": True},
    {"numero_seccion": "8", "titulo": "INDICADORES COMERCIALES", "tipo_seccion": "INFORMATIVA", "orden": 8, "es_obligatoria": True},
    {"numero_seccion": "9.1", "titulo": "CANTIDAD DE DOCUMENTOS EMITIDOS Y RECIBIDOS", "tipo_seccion": "INFORMATIVA", "orden": 9, "es_obligatoria": True},
    {"numero_seccion": "9.2", "titulo": "MONTO DE OPERACIONES REALIZADAS", "tipo_seccion": "INFORMATIVA", "orden": 10, "es_obligatoria": True},
    {"numero_seccion": "10", "titulo": "RECTIFICACIÓN", "tipo_seccion": "RECTIFICACION", "orden": 11, "es_obligatoria": False},
    {"numero_seccion": "11", "titulo": "ACCESORIOS", "tipo_seccion": "ACCESORIOS", "orden": 12, "es_obligatoria": False},
    {"numero_seccion": "12", "titulo": "CONTADOR", "tipo_seccion": "INFORMATIVA", "orden": 13, "es_obligatoria": False},
    {"numero_seccion": "13", "titulo": "CÓDIGOS", "tipo_seccion": "INFORMATIVA", "orden": 14, "es_obligatoria": False},
]

# =========================================================================
# CASILLAS - Lista completa de todas las secciones
# =========================================================================
CASILLAS_SAT_2237 = [
    # =========================================================================
    # SECCIÓN 3: DÉBITO FISCAL POR OPERACIONES LOCALES
    # =========================================================================
    {"seccion": "3", "codigo": "3.1", "nombre": "Ventas exentas y servicios exentos", "tipo_casilla": "BASE_IMPONIBLE", "formula_calculo": None, "es_editable": True},
    {"seccion": "3", "codigo": "3.2", "nombre": "Ventas de medicamentos genéricos, alternativos y antirretrovirales", "tipo_casilla": "BASE_IMPONIBLE", "formula_calculo": None, "es_editable": True},
    {"seccion": "3", "codigo": "3.3", "nombre": "Ventas no afectas realizadas a contribuyentes calificados Decreto 29-89", "tipo_casilla": "REFERENCIA", "formula_calculo": None, "es_editable": True},
    {"seccion": "3", "codigo": "3.4", "nombre": "Ventas de vehículos terrestres (2+ años anteriores)", "tipo_casilla": "BASE_IMPONIBLE", "formula_calculo": None, "es_editable": True},
    {"seccion": "3", "codigo": "3.4_D", "nombre": "Débito Fiscal vehículos terrestres (2+ años anteriores)", "tipo_casilla": "DEBITO_FISCAL", "formula_calculo": "{3.4} * 0.12", "es_editable": False},
    {"seccion": "3", "codigo": "3.5", "nombre": "Ventas de vehículos terrestres (año en curso, siguiente o anterior)", "tipo_casilla": "BASE_IMPONIBLE", "formula_calculo": None, "es_editable": True},
    {"seccion": "3", "codigo": "3.5_D", "nombre": "Débito Fiscal vehículos terrestres (recientes)", "tipo_casilla": "DEBITO_FISCAL", "formula_calculo": "{3.5} * 0.12", "es_editable": False},
    {"seccion": "3", "codigo": "3.6", "nombre": "Ventas gravadas", "tipo_casilla": "BASE_IMPONIBLE", "formula_calculo": None, "es_editable": True},
    {"seccion": "3", "codigo": "3.6_D", "nombre": "Débito Fiscal ventas gravadas", "tipo_casilla": "DEBITO_FISCAL", "formula_calculo": "{3.6} * 0.12", "es_editable": False},
    {"seccion": "3", "codigo": "3.7", "nombre": "Servicios gravados", "tipo_casilla": "BASE_IMPONIBLE", "formula_calculo": None, "es_editable": True},
    {"seccion": "3", "codigo": "3.7_D", "nombre": "Débito Fiscal servicios gravados", "tipo_casilla": "DEBITO_FISCAL", "formula_calculo": "{3.7} * 0.12", "es_editable": False},
    {"seccion": "3", "codigo": "3_SUM", "nombre": "Sumatoria de las columnas BASE y DÉBITOS", "tipo_casilla": "CALCULADO", "formula_calculo": "{3.1} + {3.2} + {3.4} + {3.5} + {3.6} + {3.7}", "es_editable": False},

    # =========================================================================
    # SECCIÓN 4: OPERACIONES DE EXPORTACIÓN Y TRANSFERENCIA
    # =========================================================================
    {"seccion": "4", "codigo": "4.1", "nombre": "Exportaciones a Centro América", "tipo_casilla": "REFERENCIA", "formula_calculo": None, "es_editable": True},
    {"seccion": "4", "codigo": "4.2", "nombre": "Exportaciones al resto del mundo", "tipo_casilla": "REFERENCIA", "formula_calculo": None, "es_editable": True},
    {"seccion": "4", "codigo": "4.3", "nombre": "Transferencias con FYDUCA", "tipo_casilla": "REFERENCIA", "formula_calculo": None, "es_editable": True},
    {"seccion": "4", "codigo": "4.4", "nombre": "Ventas de medicamentos genéricos, alternativos y antirretrovirales", "tipo_casilla": "REFERENCIA", "formula_calculo": None, "es_editable": True},
    {"seccion": "4", "codigo": "4.5", "nombre": "Ventas de vehículos terrestres (2+ años anteriores)", "tipo_casilla": "REFERENCIA", "formula_calculo": None, "es_editable": True},
    {"seccion": "4", "codigo": "4.6", "nombre": "Ventas de vehículos terrestres (año en curso, siguiente o anterior)", "tipo_casilla": "REFERENCIA", "formula_calculo": None, "es_editable": True},
    {"seccion": "4", "codigo": "4_SUM", "nombre": "Sumatoria de la columna Operaciones de Exportación y Transferencia", "tipo_casilla": "CALCULADO", "formula_calculo": "{4.1} + {4.2} + {4.3} + {4.4} + {4.5} + {4.6}", "es_editable": False},
    {"seccion": "4", "codigo": "4.7", "nombre": "Total crédito fiscal recibido Régimen Especial u Optativo (Débito)", "tipo_casilla": "DEBITO_FISCAL", "formula_calculo": None, "es_editable": True},
    {"seccion": "4", "codigo": "4.8", "nombre": "Débito facturas especiales emitidas por exportadores", "tipo_casilla": "DEBITO_FISCAL", "formula_calculo": None, "es_editable": True},
    {"seccion": "4", "codigo": "4_TOTAL", "nombre": "Total determinación del débito Fiscal", "tipo_casilla": "CALCULADO", "formula_calculo": "{4.7} + {4.8}", "es_editable": False},

    # =========================================================================
    # SECCIÓN 5: CRÉDITO FISCAL POR OPERACIONES LOCALES
    # =========================================================================
    {"seccion": "5", "codigo": "5.1", "nombre": "Compras de medicamentos genéricos, alternativos y antirretrovirales", "tipo_casilla": "BASE_IMPONIBLE", "formula_calculo": None, "es_editable": True},
    {"seccion": "5", "codigo": "5.2", "nombre": "Compras y servicios adquiridos de pequeños contribuyentes", "tipo_casilla": "BASE_IMPONIBLE", "formula_calculo": None, "es_editable": True},
    {"seccion": "5", "codigo": "5.2_C", "nombre": "Crédito Fiscal pequeños contribuyentes", "tipo_casilla": "CREDITO_FISCAL", "formula_calculo": "{5.2} * 0.04", "es_editable": False},
    {"seccion": "5", "codigo": "5.3", "nombre": "Compras que no generan derecho a compensación del crédito fiscal", "tipo_casilla": "BASE_IMPONIBLE", "formula_calculo": None, "es_editable": True},
    {"seccion": "5", "codigo": "5.4", "nombre": "Compras de vehículos terrestres (2+ años anteriores)", "tipo_casilla": "BASE_IMPONIBLE", "formula_calculo": None, "es_editable": True},
    {"seccion": "5", "codigo": "5.5", "nombre": "Compras de vehículos terrestres (año en curso, siguiente o anterior)", "tipo_casilla": "BASE_IMPONIBLE", "formula_calculo": None, "es_editable": True},
    {"seccion": "5", "codigo": "5.5_C", "nombre": "Crédito Fiscal vehículos terrestres", "tipo_casilla": "CREDITO_FISCAL", "formula_calculo": "{5.5} * 0.12", "es_editable": False},
    {"seccion": "5", "codigo": "5.6", "nombre": "Compras de combustibles", "tipo_casilla": "BASE_IMPONIBLE", "formula_calculo": None, "es_editable": True},
    {"seccion": "5", "codigo": "5.6_C", "nombre": "Crédito Fiscal combustibles", "tipo_casilla": "CREDITO_FISCAL", "formula_calculo": "{5.6} * 0.12", "es_editable": False},
    {"seccion": "5", "codigo": "5.7", "nombre": "Otras compras", "tipo_casilla": "BASE_IMPONIBLE", "formula_calculo": None, "es_editable": True},
    {"seccion": "5", "codigo": "5.7_C", "nombre": "Crédito Fiscal otras compras", "tipo_casilla": "CREDITO_FISCAL", "formula_calculo": "{5.7} * 0.12", "es_editable": False},
    {"seccion": "5", "codigo": "5.8", "nombre": "Servicios adquiridos", "tipo_casilla": "BASE_IMPONIBLE", "formula_calculo": None, "es_editable": True},
    {"seccion": "5", "codigo": "5.8_C", "nombre": "Crédito Fiscal servicios adquiridos", "tipo_casilla": "CREDITO_FISCAL", "formula_calculo": "{5.8} * 0.12", "es_editable": False},
    {"seccion": "5", "codigo": "5.9", "nombre": "Importaciones de Centro América", "tipo_casilla": "BASE_IMPONIBLE", "formula_calculo": None, "es_editable": True},
    {"seccion": "5", "codigo": "5.9_C", "nombre": "Crédito Fiscal importaciones Centro América", "tipo_casilla": "CREDITO_FISCAL", "formula_calculo": "{5.9} * 0.12", "es_editable": False},
    {"seccion": "5", "codigo": "5.10", "nombre": "Adquisiciones con FYDUCA", "tipo_casilla": "BASE_IMPONIBLE", "formula_calculo": None, "es_editable": True},
    {"seccion": "5", "codigo": "5.10_C", "nombre": "Crédito Fiscal FYDUCA", "tipo_casilla": "CREDITO_FISCAL", "formula_calculo": "{5.10} * 0.12", "es_editable": False},
    {"seccion": "5", "codigo": "5.11", "nombre": "Importaciones del resto del mundo", "tipo_casilla": "BASE_IMPONIBLE", "formula_calculo": None, "es_editable": True},
    {"seccion": "5", "codigo": "5.11_C", "nombre": "Crédito Fiscal importaciones resto del mundo", "tipo_casilla": "CREDITO_FISCAL", "formula_calculo": "{5.11} * 0.12", "es_editable": False},
    {"seccion": "5", "codigo": "5.12", "nombre": "Compras de activos fijos directamente vinculados con el proceso productivo", "tipo_casilla": "BASE_IMPONIBLE", "formula_calculo": None, "es_editable": True},
    {"seccion": "5", "codigo": "5.12_C", "nombre": "Crédito Fiscal activos fijos", "tipo_casilla": "CREDITO_FISCAL", "formula_calculo": "{5.12} * 0.12", "es_editable": False},
    {"seccion": "5", "codigo": "5.13", "nombre": "Importación de activos fijos", "tipo_casilla": "BASE_IMPONIBLE", "formula_calculo": None, "es_editable": True},
    {"seccion": "5", "codigo": "5.13_C", "nombre": "Crédito Fiscal importación activos fijos", "tipo_casilla": "CREDITO_FISCAL", "formula_calculo": "{5.13} * 0.12", "es_editable": False},
    {"seccion": "5", "codigo": "5.14", "nombre": "IVA conforme constancias de exención recibidas", "tipo_casilla": "CREDITO_FISCAL", "formula_calculo": None, "es_editable": True},
    {"seccion": "5", "codigo": "5_REM", "nombre": "Remanente de crédito fiscal del período anterior", "tipo_casilla": "REMANENTE", "formula_calculo": None, "es_editable": True},
    {"seccion": "5", "codigo": "5_SUM", "nombre": "Sumatoria de las columnas BASE y CRÉDITOS", "tipo_casilla": "CALCULADO", "formula_calculo": "{5.2_C} + {5.5_C} + {5.6_C} + {5.7_C} + {5.8_C} + {5.9_C} + {5.10_C} + {5.11_C} + {5.12_C} + {5.13_C} + {5.14} + {5_REM}", "es_editable": False},

    # =========================================================================
    # SECCIÓN 6: CRÉDITO FISCAL EXPORTACIONES
    # =========================================================================
    {"seccion": "6", "codigo": "6.1", "nombre": "Compras y servicios adquiridos de pequeño contribuyente", "tipo_casilla": "BASE_IMPONIBLE", "formula_calculo": None, "es_editable": True},
    {"seccion": "6", "codigo": "6.1_C", "nombre": "Crédito Fiscal pequeño contribuyente", "tipo_casilla": "CREDITO_FISCAL", "formula_calculo": "{6.1} * 0.04", "es_editable": False},
    {"seccion": "6", "codigo": "6.2", "nombre": "Compras de combustibles", "tipo_casilla": "BASE_IMPONIBLE", "formula_calculo": None, "es_editable": True},
    {"seccion": "6", "codigo": "6.2_C", "nombre": "Crédito Fiscal combustibles", "tipo_casilla": "CREDITO_FISCAL", "formula_calculo": "{6.2} * 0.12", "es_editable": False},
    {"seccion": "6", "codigo": "6.3", "nombre": "Otras compras", "tipo_casilla": "BASE_IMPONIBLE", "formula_calculo": None, "es_editable": True},
    {"seccion": "6", "codigo": "6.3_C", "nombre": "Crédito Fiscal otras compras", "tipo_casilla": "CREDITO_FISCAL", "formula_calculo": "{6.3} * 0.12", "es_editable": False},
    {"seccion": "6", "codigo": "6.4", "nombre": "Servicios adquiridos", "tipo_casilla": "BASE_IMPONIBLE", "formula_calculo": None, "es_editable": True},
    {"seccion": "6", "codigo": "6.4_C", "nombre": "Crédito Fiscal servicios", "tipo_casilla": "CREDITO_FISCAL", "formula_calculo": "{6.4} * 0.12", "es_editable": False},
    {"seccion": "6", "codigo": "6.5", "nombre": "Importaciones de Centro América", "tipo_casilla": "BASE_IMPONIBLE", "formula_calculo": None, "es_editable": True},
    {"seccion": "6", "codigo": "6.5_C", "nombre": "Crédito Fiscal importaciones CA", "tipo_casilla": "CREDITO_FISCAL", "formula_calculo": "{6.5} * 0.12", "es_editable": False},
    {"seccion": "6", "codigo": "6.6", "nombre": "Adquisiciones con FYDUCA", "tipo_casilla": "BASE_IMPONIBLE", "formula_calculo": None, "es_editable": True},
    {"seccion": "6", "codigo": "6.6_C", "nombre": "Crédito Fiscal FYDUCA", "tipo_casilla": "CREDITO_FISCAL", "formula_calculo": "{6.6} * 0.12", "es_editable": False},
    {"seccion": "6", "codigo": "6.7", "nombre": "Importaciones del resto del mundo", "tipo_casilla": "BASE_IMPONIBLE", "formula_calculo": None, "es_editable": True},
    {"seccion": "6", "codigo": "6.7_C", "nombre": "Crédito Fiscal importaciones resto del mundo", "tipo_casilla": "CREDITO_FISCAL", "formula_calculo": "{6.7} * 0.12", "es_editable": False},
    {"seccion": "6", "codigo": "6_RET", "nombre": "Retenciones de IVA realizadas", "tipo_casilla": "CREDITO_FISCAL", "formula_calculo": None, "es_editable": True},
    {"seccion": "6", "codigo": "6_SUM", "nombre": "Sumatoria de créditos fiscales para exportaciones", "tipo_casilla": "CALCULADO", "formula_calculo": "{6.1_C} + {6.2_C} + {6.3_C} + {6.4_C} + {6.5_C} + {6.6_C} + {6.7_C} + {6_RET}", "es_editable": False},
    {"seccion": "6", "codigo": "6_TOTAL", "nombre": "Total determinación del Crédito Fiscal", "tipo_casilla": "CALCULADO", "formula_calculo": "{6_SUM}", "es_editable": False},

    # =========================================================================
    # SECCIÓN 7: DETERMINACIÓN DEL IMPUESTO
    # =========================================================================
    {"seccion": "7", "codigo": "7.1", "nombre": "Crédito fiscal para el período siguiente por operaciones locales (Créditos mayor que Débitos)", "tipo_casilla": "CALCULADO", "formula_calculo": "CASE WHEN {5_SUM} > {3_SUM} THEN {5_SUM} - {3_SUM} ELSE 0 END", "es_editable": False},
    {"seccion": "7", "codigo": "7.2", "nombre": "Crédito fiscal por operaciones de exportación y/o transferencia (Créditos mayor que Débitos)", "tipo_casilla": "CALCULADO", "formula_calculo": "CASE WHEN {6_TOTAL} > {4_TOTAL} THEN {6_TOTAL} - {4_TOTAL} ELSE 0 END", "es_editable": False},
    {"seccion": "7", "codigo": "7.3", "nombre": "IMPUESTO TOTAL DETERMINADO Operaciones locales", "tipo_casilla": "CALCULADO", "formula_calculo": "CASE WHEN {3_SUM} > {5_SUM} THEN {3_SUM} - {5_SUM} ELSE 0 END", "es_editable": False},
    {"seccion": "7", "codigo": "7.4", "nombre": "IMPUESTO TOTAL DETERMINADO Operaciones de exportación y/o transferencia", "tipo_casilla": "CALCULADO", "formula_calculo": "CASE WHEN {4_TOTAL} > {6_TOTAL} THEN {4_TOTAL} - {6_TOTAL} ELSE 0 END", "es_editable": False},
    {"seccion": "7", "codigo": "7.5", "nombre": "Crédito fiscal para el período siguiente por operaciones de exportación y/o transferencia", "tipo_casilla": "CALCULADO", "formula_calculo": "{7.2}", "es_editable": False},
    {"seccion": "7", "codigo": "7_SALDO", "nombre": "SALDO DEL IMPUESTO", "tipo_casilla": "CALCULADO", "formula_calculo": "{7.3} + {7.4}", "es_editable": False},
    {"seccion": "7", "codigo": "7_REM", "nombre": "Remanente de retenciones del IVA del período anterior", "tipo_casilla": "REMANENTE", "formula_calculo": None, "es_editable": True},
    {"seccion": "7", "codigo": "7_REM_PER", "nombre": "Retenciones del IVA del período", "tipo_casilla": "CALCULADO", "formula_calculo": None, "es_editable": True},
    {"seccion": "7", "codigo": "7_CONST", "nombre": "IVA pagado mediante constancias de exención", "tipo_casilla": "CALCULADO", "formula_calculo": None, "es_editable": True},
    {"seccion": "7", "codigo": "7_SALDO_RET", "nombre": "Saldo de retenciones para el período siguiente", "tipo_casilla": "CALCULADO", "formula_calculo": "{7_REM_PER} - {7_CONST}", "es_editable": False},
    {"seccion": "7", "codigo": "7_PAGAR", "nombre": "IMPUESTO A PAGAR", "tipo_casilla": "CALCULADO", "formula_calculo": "{7_SALDO} - {7_SALDO_RET}", "es_editable": False},

    # =========================================================================
    # SECCIÓN 8: INDICADORES COMERCIALES
    # =========================================================================
    {"seccion": "8", "codigo": "8.1", "nombre": "Indicadores comerciales, base débitos menos base créditos", "tipo_casilla": "CALCULADO", "formula_calculo": "{3_SUM} - {5_SUM}", "es_editable": False},
    {"seccion": "8", "codigo": "8.2", "nombre": "Razón ventas y compras, base débitos dividido base créditos", "tipo_casilla": "CALCULADO", "formula_calculo": "CASE WHEN {5_SUM} > 0 THEN {3_SUM} / {5_SUM} ELSE 0 END", "es_editable": False},

    # =========================================================================
    # SECCIÓN 9.1: CANTIDAD DE DOCUMENTOS EMITIDOS Y RECIBIDOS (v2.0)
    # =========================================================================
    {"seccion": "9.1", "codigo": "9.1.1_E", "nombre": "Facturas (incluidas anuladas) - Emitidas", "tipo_casilla": "CONTEO", "formula_calculo": None, "es_editable": True},
    {"seccion": "9.1", "codigo": "9.1.1_R", "nombre": "Facturas (incluidas anuladas) - Recibidas", "tipo_casilla": "CONTEO", "formula_calculo": None, "es_editable": True},
    {"seccion": "9.1", "codigo": "9.1.2_E", "nombre": "Notas de crédito - Emitidas", "tipo_casilla": "CONTEO", "formula_calculo": None, "es_editable": True},
    {"seccion": "9.1", "codigo": "9.1.2_R", "nombre": "Notas de crédito - Recibidas", "tipo_casilla": "CONTEO", "formula_calculo": None, "es_editable": True},
    {"seccion": "9.1", "codigo": "9.1.3_E", "nombre": "Notas de débito - Emitidas", "tipo_casilla": "CONTEO", "formula_calculo": None, "es_editable": True},
    {"seccion": "9.1", "codigo": "9.1.3_R", "nombre": "Notas de débito - Recibidas", "tipo_casilla": "CONTEO", "formula_calculo": None, "es_editable": True},
    {"seccion": "9.1", "codigo": "9.1.4_E", "nombre": "Notas de abono - Emitidas", "tipo_casilla": "CONTEO", "formula_calculo": None, "es_editable": True},
    {"seccion": "9.1", "codigo": "9.1.4_R", "nombre": "Notas de abono - Recibidas", "tipo_casilla": "CONTEO", "formula_calculo": None, "es_editable": True},
    {"seccion": "9.1", "codigo": "9.1.5_E", "nombre": "Constancias de exención - Emitidas", "tipo_casilla": "CONTEO", "formula_calculo": None, "es_editable": True},
    {"seccion": "9.1", "codigo": "9.1.5_R", "nombre": "Constancias de exención - Recibidas", "tipo_casilla": "CONTEO", "formula_calculo": None, "es_editable": True},

    # =========================================================================
    # SECCIÓN 9.2: MONTO DE OPERACIONES REALIZADAS (v2.0)
    # =========================================================================
    {"seccion": "9.2", "codigo": "9.2.1_E", "nombre": "Valor de las notas de crédito del período - Emitidas", "tipo_casilla": "REFERENCIA", "formula_calculo": None, "es_editable": True},
    {"seccion": "9.2", "codigo": "9.2.1_R", "nombre": "Valor de las notas de crédito del período - Recibidas", "tipo_casilla": "REFERENCIA", "formula_calculo": None, "es_editable": True},
    {"seccion": "9.2", "codigo": "9.2.2_E", "nombre": "Valor de las notas de débito del período - Emitidas", "tipo_casilla": "REFERENCIA", "formula_calculo": None, "es_editable": True},
    {"seccion": "9.2", "codigo": "9.2.2_R", "nombre": "Valor de las notas de débito del período - Recibidas", "tipo_casilla": "REFERENCIA", "formula_calculo": None, "es_editable": True},
    {"seccion": "9.2", "codigo": "9.2.3_E", "nombre": "Valor de constancias de adquisición de insumos de producción local - Emitidas", "tipo_casilla": "REFERENCIA", "formula_calculo": None, "es_editable": True},
    {"seccion": "9.2", "codigo": "9.2.3_R", "nombre": "Valor de constancias de adquisición de insumos de producción local - Recibidas", "tipo_casilla": "REFERENCIA", "formula_calculo": None, "es_editable": True},

    # =========================================================================
    # SECCIÓN 10: RECTIFICACIÓN
    # =========================================================================
    {"seccion": "10", "codigo": "10.1", "nombre": "Número de formulario SAT-2237 que se rectifica", "tipo_casilla": "REFERENCIA", "formula_calculo": None, "es_editable": True},
    {"seccion": "10", "codigo": "10.2", "nombre": "(-) Impuesto ingresado con el formulario que se rectifica y anteriores", "tipo_casilla": "AJUSTE", "formula_calculo": None, "es_editable": True},
    {"seccion": "10", "codigo": "10.3", "nombre": "(=) Impuesto a pagar", "tipo_casilla": "CALCULADO", "formula_calculo": "{7_PAGAR} - {10.2}", "es_editable": False},
    {"seccion": "10", "codigo": "10.4", "nombre": "(=) Impuesto a favor del contribuyente", "tipo_casilla": "CALCULADO", "formula_calculo": "CASE WHEN {10.2} > {7_PAGAR} THEN {10.2} - {7_PAGAR} ELSE 0 END", "es_editable": False},

    # =========================================================================
    # SECCIÓN 11: ACCESORIOS
    # =========================================================================
    {"seccion": "11", "codigo": "11.1", "nombre": "Fecha máxima de pago sin accesorios", "tipo_casilla": "REFERENCIA", "formula_calculo": None, "es_editable": True},
    {"seccion": "11", "codigo": "11.2", "nombre": "¿Cuándo pagará este formulario?", "tipo_casilla": "REFERENCIA", "formula_calculo": None, "es_editable": True},
    {"seccion": "11", "codigo": "11.3", "nombre": "(+) Multa formal (por presentación extemporánea)", "tipo_casilla": "AJUSTE", "formula_calculo": None, "es_editable": True},
    {"seccion": "11", "codigo": "11.4", "nombre": "(+) Multa por omisión", "tipo_casilla": "AJUSTE", "formula_calculo": None, "es_editable": True},
    {"seccion": "11", "codigo": "11.5", "nombre": "(+) Multa por rectificación", "tipo_casilla": "AJUSTE", "formula_calculo": None, "es_editable": True},
    {"seccion": "11", "codigo": "11.6", "nombre": "(+) Intereses", "tipo_casilla": "AJUSTE", "formula_calculo": None, "es_editable": True},
    {"seccion": "11", "codigo": "11.7", "nombre": "(+) Mora", "tipo_casilla": "AJUSTE", "formula_calculo": None, "es_editable": True},
    {"seccion": "11", "codigo": "11_SUM", "nombre": "(=) Accesorios a Pagar", "tipo_casilla": "CALCULADO", "formula_calculo": "{11.3} + {11.4} + {11.5} + {11.6} + {11.7}", "es_editable": False},
    {"seccion": "11", "codigo": "11_TOTAL", "nombre": "TOTAL A PAGAR", "tipo_casilla": "CALCULADO", "formula_calculo": "{7_PAGAR} + {11_SUM}", "es_editable": False},

    # =========================================================================
    # SECCIÓN 12: CONTADOR
    # =========================================================================
    {"seccion": "12", "codigo": "12.1", "nombre": "NIT del contador responsable de la contabilidad del contribuyente", "tipo_casilla": "REFERENCIA", "formula_calculo": None, "es_editable": True},

    # =========================================================================
    # SECCIÓN 13: CÓDIGOS
    # =========================================================================
    {"seccion": "13", "codigo": "13.1", "nombre": "Código de anexo del detalle de facturas especiales", "tipo_casilla": "REFERENCIA", "formula_calculo": None, "es_editable": True},
    {"seccion": "13", "codigo": "13.2", "nombre": "Código resumen de facturación mensual (CRFM)", "tipo_casilla": "REFERENCIA", "formula_calculo": None, "es_editable": True},
]

# =========================================================================
# REGLAS DE FILTRADO DE FACTURAS
# Mapean las casillas con criterios para extraer datos de facturas
# =========================================================================
REGLAS_FILTRADO_SAT_2237 = [
    # Sección 3: Débito Fiscal Local
    {"casilla_codigo": "3.1", "nombre": "Ventas Exentas", "criterios_json": {"tipo_operacion": "Venta", "es_exento": True, "es_exportacion": False}, "campo_factura": "total_exento_gtq", "operacion": "SUMA", "orden": 1},
    {"casilla_codigo": "3.6", "nombre": "Ventas de Bienes Gravados", "criterios_json": {"tipo_operacion": "Venta", "es_exento": False, "es_exportacion": False, "bien_o_servicio": "B"}, "campo_factura": "total_gravado_bienes_gtq", "operacion": "SUMA", "orden": 2},
    {"casilla_codigo": "3.7", "nombre": "Ventas de Servicios Gravados", "criterios_json": {"tipo_operacion": "Venta", "es_exento": False, "es_exportacion": False, "bien_o_servicio": "S"}, "campo_factura": "total_gravado_servicios_gtq", "operacion": "SUMA", "orden": 3},

    # Sección 4: Exportaciones
    {"casilla_codigo": "4.1", "nombre": "Exportaciones a Centroamérica (excepto Honduras)", "criterios_json": {"tipo_operacion": "Venta", "es_exportacion": True, "region": "CENTROAMERICA", "pais_destino": {"$ne": "HND"}}, "campo_factura": "total_gtq", "operacion": "SUMA", "orden": 1},
    {"casilla_codigo": "4.2", "nombre": "Exportaciones al resto del mundo", "criterios_json": {"tipo_operacion": "Venta", "es_exportacion": True, "region": "FUERA_CENTROAMERICA"}, "campo_factura": "total_gtq", "operacion": "SUMA", "orden": 2},
    {"casilla_codigo": "4.3", "nombre": "Transferencias FYDUCA", "criterios_json": {"tipo_operacion": "Venta", "tipo_documento": "FYDUCA"}, "campo_factura": "total_gtq", "operacion": "SUMA", "orden": 3},

    # Sección 5: Crédito Fiscal Local
    {"casilla_codigo": "5.6", "nombre": "Compras de Combustibles", "criterios_json": {"tipo_operacion": "Compra", "clasificacion_gasto_sat": "COMBUSTIBLE"}, "campo_factura": "total_gravado_gtq", "operacion": "SUMA", "orden": 1},
    {"casilla_codigo": "5.7", "nombre": "Otras Compras (Bienes)", "criterios_json": {"tipo_operacion": "Compra", "clasificacion_gasto_sat": "NORMAL", "bien_o_servicio": "B"}, "campo_factura": "total_gravado_bienes_gtq", "operacion": "SUMA", "orden": 2},
    {"casilla_codigo": "5.8", "nombre": "Servicios Adquiridos", "criterios_json": {"tipo_operacion": "Compra", "clasificacion_gasto_sat": "NORMAL", "bien_o_servicio": "S"}, "campo_factura": "total_gravado_servicios_gtq", "operacion": "SUMA", "orden": 3},
    {"casilla_codigo": "5.12", "nombre": "Compras de Activos Fijos", "criterios_json": {"tipo_operacion": "Compra", "clasificacion_gasto_sat": "ACTIVO_FIJO"}, "campo_factura": "total_gravado_gtq", "operacion": "SUMA", "orden": 4},
]

# =========================================================================
# EXCLUSIONES
# Criterios para excluir ciertas facturas de casillas específicas
# =========================================================================
EXCLUSIONES_SAT_2237 = [
    {"casilla_codigo": "4.1", "nombre": "Excluir FYDUCA Honduras", "descripcion": "Las transferencias FYDUCA van en casilla 4.3", "criterios_exclusion_json": {"tipo_documento": "FYDUCA"}},
]

# =========================================================================
# REGÍMENES ASOCIADOS
# Códigos de RegimenFiscal que deben usar este formulario
# =========================================================================
REGIMENES_ASOCIADOS = ["RG_UTILIDADES", "PC_FEL"]