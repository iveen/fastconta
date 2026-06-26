"""
SEED: SAT-2237 - IVA GENERAL
Declaración Jurada Mensual del IVA - Régimen General
"""

SAT_2237_FORMULARIO = {
    "codigo": "SAT-2237",
    "version": "1.0",
    "nombre": "Declaración Jurada Mensual del IVA - Régimen General",
    "descripcion": "Para contribuyentes del régimen general que realizan operaciones locales y exportaciones.",
    "es_version_activa": True,
    "editable": True,
    
    "secciones": [
        # =========================================
        # SECCIÓN 1: NIT DEL CONTRIBUYENTE (Automática)
        # =========================================
        {
            "numero_seccion": "1",
            "titulo": "NIT DEL CONTRIBUYENTE",
            "tipo_seccion": "IDENTIFICACION",
            "orden": 0,
            "es_automatica": True,
            "casillas": [
                {
                    "codigo": "1.1",
                    "nombre": "NIT DEL CONTRIBUYENTE",
                    "tipo_casilla": "REFERENCIA",
                    "naturaleza": "MANUAL",
                    "orden_seccion": 0,
                    "es_editable": False,
                    "es_automatica": True,
                },
                {
                    "codigo": "1.2",
                    "nombre": "NOMBRE O RAZÓN SOCIAL",
                    "tipo_casilla": "REFERENCIA",
                    "naturaleza": "MANUAL",
                    "orden_seccion": 1,
                    "es_editable": False,
                    "es_automatica": True,
                },
            ]
        },

        # =========================================
        # SECCIÓN 2: PERÍODO DE IMPOSICIÓN (Automática)
        # =========================================
        {
            "numero_seccion": "2",
            "titulo": "PERÍODO DE IMPOSICIÓN",
            "tipo_seccion": "PERIODO",
            "orden": 1,
            "es_automatica": True,
            "casillas": [
                {
                    "codigo": "2.1",
                    "nombre": "Mes",
                    "tipo_casilla": "REFERENCIA",
                    "naturaleza": "MANUAL",
                    "orden_seccion": 0,
                    "es_editable": False,
                    "es_automatica": True,
                },
                {
                    "codigo": "2.2",
                    "nombre": "Año",
                    "tipo_casilla": "REFERENCIA",
                    "naturaleza": "MANUAL",
                    "orden_seccion": 1,
                    "es_editable": False,
                    "es_automatica": True,
                },
            ]
        },

        # =========================================
        # SECCIÓN 3: DÉBITO FISCAL POR OPERACIONES LOCALES
        # =========================================
        {
            "numero_seccion": "3",
            "titulo": "DÉBITO FISCAL POR OPERACIONES LOCALES",
            "tipo_seccion": "DEBITO_FISCAL",
            "orden": 2,
            "es_automatica": True,
            "casillas": [
                # BASE IMPONIBLE (Inputs)
                {"codigo": "3.1", "nombre": "Ventas exentas y servicios exentos", "tipo_casilla": "BASE_IMPONIBLE", "naturaleza": "SUMA", "orden_seccion": 0, "es_editable": True, "es_automatica": False},
                {"codigo": "3.2", "nombre": "Ventas de medicamentos genéricos, alternativos y antirretrovirales", "tipo_casilla": "BASE_IMPONIBLE", "naturaleza": "SUMA", "orden_seccion": 1, "es_editable": True, "es_automatica": False},
                {"codigo": "3.3", "nombre": "Ventas no afectas (Decreto 29-89)", "tipo_casilla": "BASE_IMPONIBLE", "naturaleza": "SUMA", "orden_seccion": 2, "es_editable": True, "es_automatica": False},
                {"codigo": "3.4", "nombre": "Ventas de vehículos terrestres (modelo 2+ años anteriores)", "tipo_casilla": "BASE_IMPONIBLE", "naturaleza": "SUMA", "orden_seccion": 3, "es_editable": True, "es_automatica": False},
                {"codigo": "3.5", "nombre": "Ventas de vehículos terrestres (modelo año en curso/siguiente/anterior)", "tipo_casilla": "BASE_IMPONIBLE", "naturaleza": "SUMA", "orden_seccion": 4, "es_editable": True, "es_automatica": False},
                {"codigo": "3.6", "nombre": "Ventas gravadas", "tipo_casilla": "BASE_IMPONIBLE", "naturaleza": "SUMA", "orden_seccion": 5, "es_editable": True, "es_automatica": False},
                {"codigo": "3.7", "nombre": "Servicios gravados", "tipo_casilla": "BASE_IMPONIBLE", "naturaleza": "SUMA", "orden_seccion": 6, "es_editable": True, "es_automatica": False},
                
                # DÉBITO FISCAL (Calculados - 12%)
                {"codigo": "3.5_D", "nombre": "Débito Fiscal vehículos terrestres", "tipo_casilla": "DEBITO_FISCAL", "naturaleza": "PORCENTAJE", "orden_seccion": 7, "es_editable": False, "es_automatica": True, "formula_calculo": "3.5 * 0.12", "dependencias": ["3.5"]},
                {"codigo": "3.6_D", "nombre": "Débito Fiscal ventas gravadas", "tipo_casilla": "DEBITO_FISCAL", "naturaleza": "PORCENTAJE", "orden_seccion": 8, "es_editable": False, "es_automatica": True, "formula_calculo": "3.6 * 0.12", "dependencias": ["3.6"]},
                {"codigo": "3.7_D", "nombre": "Débito Fiscal servicios gravados", "tipo_casilla": "DEBITO_FISCAL", "naturaleza": "PORCENTAJE", "orden_seccion": 9, "es_editable": False, "es_automatica": True, "formula_calculo": "3.7 * 0.12", "dependencias": ["3.7"]},
                
                # TOTALES
                {"codigo": "3_SUM", "nombre": "Sumatoria Columna BASE", "tipo_casilla": "CALCULADO", "naturaleza": "SUMA", "orden_seccion": 10, "es_editable": False, "es_automatica": True, "formula_calculo": "3.1 + 3.2 + 3.3 + 3.4 + 3.5 + 3.6 + 3.7", "dependencias": ["3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7"]},
                {"codigo": "3_SUM_D", "nombre": "Sumatoria Columna DÉBITOS", "tipo_casilla": "CALCULADO", "naturaleza": "SUMA", "orden_seccion": 11, "es_editable": False, "es_automatica": True, "formula_calculo": "3.5_D + 3.6_D + 3.7_D", "dependencias": ["3.5_D", "3.6_D", "3.7_D"]},
            ]
        },

        # =========================================
        # SECCIÓN 4: OPERACIONES DE EXPORTACIÓN Y TRANSFERENCIA
        # =========================================
        {
            "numero_seccion": "4",
            "titulo": "OPERACIONES DE EXPORTACIÓN Y TRANSFERENCIA",
            "tipo_seccion": "EXPORTACIONES",
            "orden": 3,
            "es_automatica": True,
            "casillas": [
                {"codigo": "4.1", "nombre": "Exportaciones a Centro América", "tipo_casilla": "BASE_IMPONIBLE", "naturaleza": "SUMA", "orden_seccion": 0, "es_editable": True, "es_automatica": False},
                {"codigo": "4.2", "nombre": "Exportaciones al resto del mundo", "tipo_casilla": "BASE_IMPONIBLE", "naturaleza": "SUMA", "orden_seccion": 1, "es_editable": True, "es_automatica": False},
                {"codigo": "4.3", "nombre": "Transferencias con FYDUCA", "tipo_casilla": "BASE_IMPONIBLE", "naturaleza": "SUMA", "orden_seccion": 2, "es_editable": True, "es_automatica": False},
                {"codigo": "4.4", "nombre": "Ventas de medicamentos (Exportaciones)", "tipo_casilla": "BASE_IMPONIBLE", "naturaleza": "SUMA", "orden_seccion": 3, "es_editable": True, "es_automatica": False},
                {"codigo": "4.5", "nombre": "Ventas de vehículos terrestres (Exportaciones)", "tipo_casilla": "BASE_IMPONIBLE", "naturaleza": "SUMA", "orden_seccion": 4, "es_editable": True, "es_automatica": False},
                
                {"codigo": "4.5_D", "nombre": "Débito Fiscal vehículos (Exportaciones)", "tipo_casilla": "DEBITO_FISCAL", "naturaleza": "PORCENTAJE", "orden_seccion": 5, "es_editable": False, "es_automatica": True, "formula_calculo": "4.5 * 0.12", "dependencias": ["4.5"]},
                
                {"codigo": "4_SUM", "nombre": "Sumatoria Base Exportaciones", "tipo_casilla": "CALCULADO", "naturaleza": "SUMA", "orden_seccion": 6, "es_editable": False, "es_automatica": True, "formula_calculo": "4.1 + 4.2 + 4.3 + 4.4 + 4.5", "dependencias": ["4.1", "4.2", "4.3", "4.4", "4.5"]},
                {"codigo": "4_SUM_D", "nombre": "Sumatoria Débito Exportaciones", "tipo_casilla": "CALCULADO", "naturaleza": "SUMA", "orden_seccion": 7, "es_editable": False, "es_automatica": True, "formula_calculo": "4.5_D", "dependencias": ["4.5_D"]},
                
                # Ajustes Especiales
                {"codigo": "4.7", "nombre": "Crédito fiscal recibido (Régimen Especial Exportadores)", "tipo_casilla": "CREDITO_FISCAL", "naturaleza": "SUMA", "orden_seccion": 8, "es_editable": True, "es_automatica": False},
                {"codigo": "4.8", "nombre": "Débito facturas especiales (Exportadores)", "tipo_casilla": "DEBITO_FISCAL", "naturaleza": "SUMA", "orden_seccion": 9, "es_editable": True, "es_automatica": False},
                
                {"codigo": "4_TOTAL", "nombre": "Total determinación del Débito Fiscal", "tipo_casilla": "CALCULADO", "naturaleza": "SUMA", "orden_seccion": 10, "es_editable": False, "es_automatica": True, "formula_calculo": "3_SUM_D + 4_SUM_D + 4.8 + 4.7", "dependencias": ["3_SUM_D", "4_SUM_D", "4.7", "4.8"]},
            ]
        },

        # =========================================
        # SECCIÓN 5: CRÉDITO FISCAL POR OPERACIONES LOCALES
        # =========================================
        {
            "numero_seccion": "5",
            "titulo": "CRÉDITO FISCAL POR OPERACIONES LOCALES",
            "tipo_seccion": "CREDITO_FISCAL",
            "orden": 4,
            "es_automatica": True,
            "casillas": [
                # Sin derecho a crédito
                {"codigo": "5.1", "nombre": "Compras de medicamentos genéricos", "tipo_casilla": "BASE_IMPONIBLE", "naturaleza": "SUMA", "orden_seccion": 0, "es_editable": True, "es_automatica": False},
                {"codigo": "5.2", "nombre": "Compras de pequeños contribuyentes", "tipo_casilla": "BASE_IMPONIBLE", "naturaleza": "SUMA", "orden_seccion": 1, "es_editable": True, "es_automatica": False},
                {"codigo": "5.3", "nombre": "Compras que no generan derecho a compensación", "tipo_casilla": "BASE_IMPONIBLE", "naturaleza": "SUMA", "orden_seccion": 2, "es_editable": True, "es_automatica": False},
                
                # Con derecho a crédito
                {"codigo": "5.4", "nombre": "Compras de vehículos terrestres (2+ años)", "tipo_casilla": "BASE_IMPONIBLE", "naturaleza": "SUMA", "orden_seccion": 3, "es_editable": True, "es_automatica": False},
                {"codigo": "5.5", "nombre": "Compras de vehículos terrestres (recientes)", "tipo_casilla": "BASE_IMPONIBLE", "naturaleza": "SUMA", "orden_seccion": 4, "es_editable": True, "es_automatica": False},
                {"codigo": "5.6", "nombre": "Compras de combustibles", "tipo_casilla": "BASE_IMPONIBLE", "naturaleza": "SUMA", "orden_seccion": 5, "es_editable": True, "es_automatica": False},
                {"codigo": "5.7", "nombre": "Otras compras", "tipo_casilla": "BASE_IMPONIBLE", "naturaleza": "SUMA", "orden_seccion": 6, "es_editable": True, "es_automatica": False},
                {"codigo": "5.8", "nombre": "Servicios adquiridos", "tipo_casilla": "BASE_IMPONIBLE", "naturaleza": "SUMA", "orden_seccion": 7, "es_editable": True, "es_automatica": False},
                
                # CRÉDITO FISCAL (Calculados)
                {"codigo": "5.5_C", "nombre": "Crédito Fiscal compras vehículos", "tipo_casilla": "CREDITO_FISCAL", "naturaleza": "PORCENTAJE", "orden_seccion": 8, "es_editable": False, "es_automatica": True, "formula_calculo": "5.5 * 0.12", "dependencias": ["5.5"]},
                {"codigo": "5.6_C", "nombre": "Crédito Fiscal combustibles", "tipo_casilla": "CREDITO_FISCAL", "naturaleza": "PORCENTAJE", "orden_seccion": 9, "es_editable": False, "es_automatica": True, "formula_calculo": "5.6 * 0.12", "dependencias": ["5.6"]},
                {"codigo": "5.7_C", "nombre": "Crédito Fiscal otras compras", "tipo_casilla": "CREDITO_FISCAL", "naturaleza": "PORCENTAJE", "orden_seccion": 10, "es_editable": False, "es_automatica": True, "formula_calculo": "5.7 * 0.12", "dependencias": ["5.7"]},
                {"codigo": "5.8_C", "nombre": "Crédito Fiscal servicios adquiridos", "tipo_casilla": "CREDITO_FISCAL", "naturaleza": "PORCENTAJE", "orden_seccion": 11, "es_editable": False, "es_automatica": True, "formula_calculo": "5.8 * 0.12", "dependencias": ["5.8"]},
                
                # TOTALES
                {"codigo": "5_SUM", "nombre": "Sumatoria Columna BASE", "tipo_casilla": "CALCULADO", "naturaleza": "SUMA", "orden_seccion": 12, "es_editable": False, "es_automatica": True, "formula_calculo": "5.1 + 5.2 + 5.3 + 5.4 + 5.5 + 5.6 + 5.7 + 5.8", "dependencias": ["5.1", "5.2", "5.3", "5.4", "5.5", "5.6", "5.7", "5.8"]},
                {"codigo": "5_SUM_C", "nombre": "Sumatoria Columna CRÉDITOS", "tipo_casilla": "CALCULADO", "naturaleza": "SUMA", "orden_seccion": 13, "es_editable": False, "es_automatica": True, "formula_calculo": "5.5_C + 5.6_C + 5.7_C + 5.8_C", "dependencias": ["5.5_C", "5.6_C", "5.7_C", "5.8_C"]},
            ]
        },

        # =========================================
        # SECCIÓN 6: CRÉDITO FISCAL POR EXPORTACIÓN
        # =========================================
        {
            "numero_seccion": "6",
            "titulo": "CRÉDITO FISCAL POR OPERACIONES DE EXPORTACIÓN Y TRANSFERENCIA",
            "tipo_seccion": "EXPORTACIONES",
            "orden": 5,
            "es_automatica": True,
            "casillas": [
                {"codigo": "6.1", "nombre": "Compras de pequeños contribuyentes (Exportaciones)", "tipo_casilla": "BASE_IMPONIBLE", "naturaleza": "SUMA", "orden_seccion": 0, "es_editable": True, "es_automatica": False},
                {"codigo": "6.2", "nombre": "Compras de combustibles (Exportaciones)", "tipo_casilla": "BASE_IMPONIBLE", "naturaleza": "SUMA", "orden_seccion": 1, "es_editable": True, "es_automatica": False},
                {"codigo": "6.3", "nombre": "Otras compras (Exportaciones)", "tipo_casilla": "BASE_IMPONIBLE", "naturaleza": "SUMA", "orden_seccion": 2, "es_editable": True, "es_automatica": False},
                {"codigo": "6.4", "nombre": "Servicios adquiridos (Exportaciones)", "tipo_casilla": "BASE_IMPONIBLE", "naturaleza": "SUMA", "orden_seccion": 3, "es_editable": True, "es_automatica": False},
                
                {"codigo": "6.2_C", "nombre": "Crédito Fiscal combustibles (Exportaciones)", "tipo_casilla": "CREDITO_FISCAL", "naturaleza": "PORCENTAJE", "orden_seccion": 4, "es_editable": False, "es_automatica": True, "formula_calculo": "6.2 * 0.12", "dependencias": ["6.2"]},
                {"codigo": "6.3_C", "nombre": "Crédito Fiscal otras compras (Exportaciones)", "tipo_casilla": "CREDITO_FISCAL", "naturaleza": "PORCENTAJE", "orden_seccion": 5, "es_editable": False, "es_automatica": True, "formula_calculo": "6.3 * 0.12", "dependencias": ["6.3"]},
                {"codigo": "6.4_C", "nombre": "Crédito Fiscal servicios (Exportaciones)", "tipo_casilla": "CREDITO_FISCAL", "naturaleza": "PORCENTAJE", "orden_seccion": 6, "es_editable": False, "es_automatica": True, "formula_calculo": "6.4 * 0.12", "dependencias": ["6.4"]},
                
                {"codigo": "6_REMANENTE", "nombre": "Remanente de crédito fiscal del período anterior por exportaciones", "tipo_casilla": "REMANENTE", "naturaleza": "SUMA", "orden_seccion": 7, "es_editable": True, "es_automatica": False},
                
                {"codigo": "6_SUM", "nombre": "Sumatoria Base Exportaciones", "tipo_casilla": "CALCULADO", "naturaleza": "SUMA", "orden_seccion": 8, "es_editable": False, "es_automatica": True, "formula_calculo": "6.1 + 6.2 + 6.3 + 6.4", "dependencias": ["6.1", "6.2", "6.3", "6.4"]},
                {"codigo": "6_SUM_C", "nombre": "Total determinación del Crédito Fiscal", "tipo_casilla": "CALCULADO", "naturaleza": "SUMA", "orden_seccion": 9, "es_editable": False, "es_automatica": True, "formula_calculo": "6.2_C + 6.3_C + 6.4_C + 6_REMANENTE", "dependencias": ["6.2_C", "6.3_C", "6.4_C", "6_REMANENTE"]},
            ]
        },

        # =========================================
        # SECCIÓN 7: DETERMINACIÓN DEL IMPUESTO
        # =========================================
        {
            "numero_seccion": "7",
            "titulo": "DETERMINACIÓN DEL CRÉDITO FISCAL O IMPUESTO A PAGAR",
            "tipo_seccion": "DETERMINACION",
            "orden": 6,
            "es_automatica": True,
            "casillas": [
                {"codigo": "7.3", "nombre": "IMPUESTO TOTAL DETERMINADO (Débito > Crédito) Operaciones Locales", "tipo_casilla": "CALCULADO", "naturaleza": "RESTA", "orden_seccion": 0, "es_editable": False, "es_automatica": True, "formula_calculo": "MAX(0, 3_SUM_D - 5_SUM_C)", "dependencias": ["3_SUM_D", "5_SUM_C"]},
                {"codigo": "7.4", "nombre": "IMPUESTO TOTAL DETERMINADO (Débito > Crédito) Operaciones Exportación", "tipo_casilla": "CALCULADO", "naturaleza": "RESTA", "orden_seccion": 1, "es_editable": False, "es_automatica": True, "formula_calculo": "MAX(0, 4_SUM_D - 6_SUM_C)", "dependencias": ["4_SUM_D", "6_SUM_C"]},
                
                {"codigo": "7.6", "nombre": "SALDO DEL IMPUESTO", "tipo_casilla": "CALCULADO", "naturaleza": "RESTA", "orden_seccion": 2, "es_editable": False, "es_automatica": True, "formula_calculo": "(3_SUM_D + 4_SUM_D) - (5_SUM_C + 6_SUM_C)", "dependencias": ["3_SUM_D", "4_SUM_D", "5_SUM_C", "6_SUM_C"]},
                
                {"codigo": "7.7", "nombre": "Remanente de retenciones del IVA del período anterior", "tipo_casilla": "REMANENTE", "naturaleza": "MANUAL", "orden_seccion": 3, "es_editable": True, "es_automatica": False},
                {"codigo": "7.10", "nombre": "(-) Constancias de retenciones del IVA recibidas en el período", "tipo_casilla": "MANUAL", "naturaleza": "RESTA", "orden_seccion": 4, "es_editable": True, "es_automatica": False},
                
                {"codigo": "7.12", "nombre": "IMPUESTO A PAGAR", "tipo_casilla": "CALCULADO", "naturaleza": "RESTA", "orden_seccion": 5, "es_editable": False, "es_automatica": True, "formula_calculo": "MAX(0, 7.6 - 7.10)", "dependencias": ["7.6", "7.10"]},
            ]
        },

        # =========================================
        # SECCIÓN 8: INDICADORES COMERCIALES
        # =========================================
        {
            "numero_seccion": "8",
            "titulo": "INDICADORES COMERCIALES",
            "tipo_seccion": "INFORMATIVA",
            "orden": 7,
            "es_automatica": True,
            "casillas": [
                {"codigo": "8.1", "nombre": "Indicadores comerciales (Base Débitos - Base Créditos)", "tipo_casilla": "CALCULADO", "naturaleza": "RESTA", "orden_seccion": 0, "es_editable": False, "es_automatica": True, "formula_calculo": "3_SUM - (5_SUM + 6_SUM)", "dependencias": ["3_SUM", "5_SUM", "6_SUM"]},
                {"codigo": "8.2", "nombre": "Razón ventas y compras", "tipo_casilla": "CALCULADO", "naturaleza": "PORCENTAJE", "orden_seccion": 1, "es_editable": False, "es_automatica": True, "formula_calculo": "IF((5_SUM + 6_SUM) > 0, 3_SUM / (5_SUM + 6_SUM), 0)", "dependencias": ["3_SUM", "5_SUM", "6_SUM"]},
            ]
        },

        # =========================================
        # SECCIÓN 9: ESTADÍSTICAS
        # =========================================
        {
            "numero_seccion": "9",
            "titulo": "ESTADÍSTICAS",
            "tipo_seccion": "INFORMATIVA",
            "orden": 8,
            "es_automatica": True,
            "casillas": [
                {"codigo": "9.1.1_E", "nombre": "Facturas Emitidas", "tipo_casilla": "MANUAL", "naturaleza": "CONTEO", "orden_seccion": 0, "es_editable": True, "es_automatica": False},
                {"codigo": "9.1.1_R", "nombre": "Facturas Recibidas", "tipo_casilla": "MANUAL", "naturaleza": "CONTEO", "orden_seccion": 1, "es_editable": True, "es_automatica": False},
                {"codigo": "9.1.7_E", "nombre": "Notas de Crédito Emitidas", "tipo_casilla": "MANUAL", "naturaleza": "CONTEO", "orden_seccion": 2, "es_editable": True, "es_automatica": False},
                {"codigo": "9.1.7_R", "nombre": "Notas de Crédito Recibidas", "tipo_casilla": "MANUAL", "naturaleza": "CONTEO", "orden_seccion": 3, "es_editable": True, "es_automatica": False},
                
                {"codigo": "9.2.1_E", "nombre": "Valor de Notas de Crédito Emitidas", "tipo_casilla": "MANUAL", "naturaleza": "SUMA", "orden_seccion": 4, "es_editable": True, "es_automatica": False},
                {"codigo": "9.2.1_R", "nombre": "Valor de Notas de Crédito Recibidas", "tipo_casilla": "MANUAL", "naturaleza": "SUMA", "orden_seccion": 5, "es_editable": True, "es_automatica": False},
            ]
        },
    ]
}