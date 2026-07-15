"""
Estructura de datos del Formulario SAT-2237 (IVA General)
Versión 2.0 (Activa 2026): Incluye secciones 9.1 y 9.2 separadas.
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
    {"numero_seccion": "9.2", "titulo": "MONTO DE OPERACIONES REALIZADAS", "tipo_seccion": "INFORMATIVA", "orden": 9, "es_obligatoria": True},
    {"numero_seccion": "10", "titulo": "RECTIFICACIÓN", "tipo_seccion": "RECTIFICACION", "orden": 10, "es_obligatoria": False},
    {"numero_seccion": "11", "titulo": "ACCESORIOS", "tipo_seccion": "ACCESORIOS", "orden": 11, "es_obligatoria": False},
    {"numero_seccion": "12", "titulo": "CONTADOR", "tipo_seccion": "INFORMATIVA", "orden": 12, "es_obligatoria": False},
    {"numero_seccion": "13", "titulo": "CÓDIGOS", "tipo_seccion": "INFORMATIVA", "orden": 13, "es_obligatoria": False},
]

# Ejemplo condensado de casillas (puedes expandir esto con todas las de tu archivo original)
# La clave es que 'seccion' debe coincidir con 'numero_seccion' de arriba.
CASILLAS_SAT_2237 = [
    # Sección 3
    {"seccion": "3", "codigo": "3.1", "nombre": "Ventas exentas y servicios exentos", "tipo_casilla": "BASE_IMPONIBLE", "formula_calculo": None, "es_editable": True},
    {"seccion": "3", "codigo": "3.6", "nombre": "Ventas gravadas", "tipo_casilla": "BASE_IMPONIBLE", "formula_calculo": None, "es_editable": True},
    {"seccion": "3", "codigo": "3_SUM", "nombre": "Sumatoria de las columnas BASE y DÉBITOS", "tipo_casilla": "CALCULADO", "formula_calculo": "{3.1} + {3.6}", "es_editable": False},
    
    # Sección 9.1 (Conteos)
    {"seccion": "9.1", "codigo": "9.1.1", "nombre": "Facturas (incluidas anuladas) - Emitidas", "tipo_casilla": "CONTEO", "formula_calculo": None, "es_editable": True},
    {"seccion": "9.1", "codigo": "9.1.2", "nombre": "Facturas (incluidas anuladas) - Recibidas", "tipo_casilla": "CONTEO", "formula_calculo": None, "es_editable": True},
    
    # Sección 9.2 (Montos)
    {"seccion": "9.2", "codigo": "9.2.1", "nombre": "Valor de las notas de crédito del período - Emitidos", "tipo_casilla": "REFERENCIA", "formula_calculo": None, "es_editable": True},
    {"seccion": "9.2", "codigo": "9.2.2", "nombre": "Valor de las notas de débito del período - Emitidos", "tipo_casilla": "REFERENCIA", "formula_calculo": None, "es_editable": True},
]

REGLAS_FILTRADO_SAT_2237 = [
    {"casilla_codigo": "3.1", "nombre": "Ventas Exentas", "criterios_json": {"tipo_operacion": "Venta", "es_exento": True}, "campo_factura": "total_exento_gtq", "operacion": "SUMA", "orden": 1},
    {"casilla_codigo": "3.6", "nombre": "Ventas de Bienes Gravados", "criterios_json": {"tipo_operacion": "Venta", "es_exento": False, "bien_o_servicio": "B"}, "campo_factura": "total_gravado_bienes_gtq", "operacion": "SUMA", "orden": 2},
]

EXCLUSIONES_SAT_2237 = [
    {"casilla_codigo": "4.1", "nombre": "Excluir FYDUCA Honduras", "descripcion": "Las transferencias FYDUCA van en casilla 4.3", "criterios_exclusion_json": {"tipo_documento": "FYDUCA"}},
]

REGIMENES_ASOCIADOS = ["RG_UTILIDADES", "PC_FEL"] # Códigos de RegimenFiscal