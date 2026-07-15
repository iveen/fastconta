"""
Catálogo base de Plan de Cuentas para FastConta.
Alineado a NIIF y requisitos fiscales de Guatemala (SAT).
Incluye contabilidad de costos (proceso fabril) y centros de gasto.

Estructura jerárquica:
- Nivel 1: Grupo principal (ACTIVO, PASIVO, PATRIMONIO, INGRESOS, GASTOS)
- Nivel 2: Subgrupos (Activo Corriente, Activo No Corriente, etc.)
- Nivel 3: Cuentas de mayor
- Nivel 4: Subcuentas detalladas
"""

PLAN_CUENTAS_BASE = [
    # ============================================================
    # ACTIVO (1000-1999)
    # ============================================================
    {"codigo": "1000", "nombre": "ACTIVO", "tipo": "activo", "naturaleza": "deudora", "nivel": 1, "acepta_tercero": False},
    
    # Nivel 2: Subgrupos de Activo
    {"codigo": "1100", "nombre": "Activo Corriente", "tipo": "activo", "naturaleza": "deudora", "nivel": 2, "acepta_tercero": False, "padre": "1000"},
    {"codigo": "1200", "nombre": "Activo No Corriente", "tipo": "activo", "naturaleza": "deudora", "nivel": 2, "acepta_tercero": False, "padre": "1000"},
    
    # Nivel 3: Cuentas de Activo Corriente
    {"codigo": "1110", "nombre": "Efectivo y Equivalentes de Efectivo", "tipo": "activo", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "1100"},
    {"codigo": "1111", "nombre": "Caja General", "tipo": "activo", "naturaleza": "deudora", "nivel": 4, "acepta_tercero": False, "padre": "1110"},
    {"codigo": "1112", "nombre": "Bancos Moneda Nacional", "tipo": "activo", "naturaleza": "deudora", "nivel": 4, "acepta_tercero": False, "padre": "1110"},
    {"codigo": "1113", "nombre": "Bancos Moneda Extranjera", "tipo": "activo", "naturaleza": "deudora", "nivel": 4, "acepta_tercero": False, "padre": "1110"},
    
    {"codigo": "1120", "nombre": "Inversiones Temporales", "tipo": "activo", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "1100"},
    
    {"codigo": "1130", "nombre": "Cuentas por Cobrar Comerciales", "tipo": "activo", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "1100"},
    {"codigo": "1131", "nombre": "Clientes Locales", "tipo": "activo", "naturaleza": "deudora", "nivel": 4, "acepta_tercero": True, "padre": "1130"},
    {"codigo": "1132", "nombre": "Clientes Exportación", "tipo": "activo", "naturaleza": "deudora", "nivel": 4, "acepta_tercero": True, "padre": "1130"},
    {"codigo": "1133", "nombre": "Documentos por Cobrar", "tipo": "activo", "naturaleza": "deudora", "nivel": 4, "acepta_tercero": True, "padre": "1130"},
    {"codigo": "1134", "nombre": "Estimación Cuentas Incobrables", "tipo": "activo", "naturaleza": "acreedora", "nivel": 4, "acepta_tercero": False, "padre": "1130"},
    
    {"codigo": "1140", "nombre": "Inventarios", "tipo": "activo", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "1100"},
    {"codigo": "1141", "nombre": "Materia Prima", "tipo": "activo", "naturaleza": "deudora", "nivel": 4, "acepta_tercero": False, "padre": "1140"},
    {"codigo": "1142", "nombre": "Producto en Proceso", "tipo": "activo", "naturaleza": "deudora", "nivel": 4, "acepta_tercero": False, "padre": "1140"},
    {"codigo": "1143", "nombre": "Producto Terminado", "tipo": "activo", "naturaleza": "deudora", "nivel": 4, "acepta_tercero": False, "padre": "1140"},
    {"codigo": "1144", "nombre": "Mercaderías", "tipo": "activo", "naturaleza": "deudora", "nivel": 4, "acepta_tercero": False, "padre": "1140"},
    {"codigo": "1145", "nombre": "Materiales de Empaque", "tipo": "activo", "naturaleza": "deudora", "nivel": 4, "acepta_tercero": False, "padre": "1140"},
    
    {"codigo": "1150", "nombre": "Anticipos a Proveedores", "tipo": "activo", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": True, "padre": "1100"},
    
    {"codigo": "1160", "nombre": "Impuestos Recuperables", "tipo": "activo", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "1100"},
    {"codigo": "1161", "nombre": "Crédito Fiscal IVA", "tipo": "activo", "naturaleza": "deudora", "nivel": 4, "acepta_tercero": False, "padre": "1160"},
    {"codigo": "1162", "nombre": "Retenciones ISR por Recuperar", "tipo": "activo", "naturaleza": "deudora", "nivel": 4, "acepta_tercero": False, "padre": "1160"},
    {"codigo": "1163", "nombre": "Anticipo ISR", "tipo": "activo", "naturaleza": "deudora", "nivel": 4, "acepta_tercero": False, "padre": "1160"},
    
    # Nivel 3: Cuentas de Activo No Corriente
    {"codigo": "1210", "nombre": "Propiedad, Planta y Equipo", "tipo": "activo", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "1200"},
    {"codigo": "1211", "nombre": "Terrenos", "tipo": "activo", "naturaleza": "deudora", "nivel": 4, "acepta_tercero": False, "padre": "1210"},
    {"codigo": "1212", "nombre": "Edificios", "tipo": "activo", "naturaleza": "deudora", "nivel": 4, "acepta_tercero": False, "padre": "1210"},
    {"codigo": "1213", "nombre": "Depreciación Acumulada Edificios", "tipo": "activo", "naturaleza": "acreedora", "nivel": 4, "acepta_tercero": False, "padre": "1210"},
    {"codigo": "1214", "nombre": "Maquinaria y Equipo Industrial", "tipo": "activo", "naturaleza": "deudora", "nivel": 4, "acepta_tercero": False, "padre": "1210"},
    {"codigo": "1215", "nombre": "Depreciación Acumulada Maquinaria", "tipo": "activo", "naturaleza": "acreedora", "nivel": 4, "acepta_tercero": False, "padre": "1210"},
    {"codigo": "1216", "nombre": "Equipo de Transporte", "tipo": "activo", "naturaleza": "deudora", "nivel": 4, "acepta_tercero": False, "padre": "1210"},
    {"codigo": "1217", "nombre": "Depreciación Acumulada Transporte", "tipo": "activo", "naturaleza": "acreedora", "nivel": 4, "acepta_tercero": False, "padre": "1210"},
    {"codigo": "1218", "nombre": "Mobiliario y Equipo de Oficina", "tipo": "activo", "naturaleza": "deudora", "nivel": 4, "acepta_tercero": False, "padre": "1210"},
    {"codigo": "1219", "nombre": "Depreciación Acumulada Mobiliario", "tipo": "activo", "naturaleza": "acreedora", "nivel": 4, "acepta_tercero": False, "padre": "1210"},
    {"codigo": "1220", "nombre": "Equipo de Cómputo", "tipo": "activo", "naturaleza": "deudora", "nivel": 4, "acepta_tercero": False, "padre": "1210"},
    {"codigo": "1221", "nombre": "Depreciación Acumulada Cómputo", "tipo": "activo", "naturaleza": "acreedora", "nivel": 4, "acepta_tercero": False, "padre": "1210"},
    
    {"codigo": "1230", "nombre": "Activos Intangibles", "tipo": "activo", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "1200"},
    {"codigo": "1231", "nombre": "Patentes y Marcas", "tipo": "activo", "naturaleza": "deudora", "nivel": 4, "acepta_tercero": False, "padre": "1230"},
    {"codigo": "1232", "nombre": "Amortización Acumulada Intangibles", "tipo": "activo", "naturaleza": "acreedora", "nivel": 4, "acepta_tercero": False, "padre": "1230"},
    {"codigo": "1233", "nombre": "Software y Licencias", "tipo": "activo", "naturaleza": "deudora", "nivel": 4, "acepta_tercero": False, "padre": "1230"},
    
    {"codigo": "1240", "nombre": "Otras Inversiones Permanentes", "tipo": "activo", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "1200"},

    # ============================================================
    # PASIVO (2000-2999)
    # ============================================================
    {"codigo": "2000", "nombre": "PASIVO", "tipo": "pasivo", "naturaleza": "acreedora", "nivel": 1, "acepta_tercero": False},
    
    {"codigo": "2100", "nombre": "Pasivo Corriente", "tipo": "pasivo", "naturaleza": "acreedora", "nivel": 2, "acepta_tercero": False, "padre": "2000"},
    {"codigo": "2200", "nombre": "Pasivo No Corriente", "tipo": "pasivo", "naturaleza": "acreedora", "nivel": 2, "acepta_tercero": False, "padre": "2000"},
    
    # Pasivo Corriente
    {"codigo": "2110", "nombre": "Cuentas por Pagar Comerciales", "tipo": "pasivo", "naturaleza": "acreedora", "nivel": 3, "acepta_tercero": False, "padre": "2100"},
    {"codigo": "2111", "nombre": "Proveedores Locales", "tipo": "pasivo", "naturaleza": "acreedora", "nivel": 4, "acepta_tercero": True, "padre": "2110"},
    {"codigo": "2112", "nombre": "Proveedores Extranjeros", "tipo": "pasivo", "naturaleza": "acreedora", "nivel": 4, "acepta_tercero": True, "padre": "2110"},
    {"codigo": "2113", "nombre": "Documentos por Pagar", "tipo": "pasivo", "naturaleza": "acreedora", "nivel": 4, "acepta_tercero": True, "padre": "2110"},
    
    {"codigo": "2120", "nombre": "Obligaciones Laborales", "tipo": "pasivo", "naturaleza": "acreedora", "nivel": 3, "acepta_tercero": False, "padre": "2100"},
    {"codigo": "2121", "nombre": "Salarios por Pagar", "tipo": "pasivo", "naturaleza": "acreedora", "nivel": 4, "acepta_tercero": False, "padre": "2120"},
    {"codigo": "2122", "nombre": "Aguinaldo por Pagar", "tipo": "pasivo", "naturaleza": "acreedora", "nivel": 4, "acepta_tercero": False, "padre": "2120"},
    {"codigo": "2123", "nombre": "Bono 14 por Pagar", "tipo": "pasivo", "naturaleza": "acreedora", "nivel": 4, "acepta_tercero": False, "padre": "2120"},
    {"codigo": "2124", "nombre": "Vacaciones por Pagar", "tipo": "pasivo", "naturaleza": "acreedora", "nivel": 4, "acepta_tercero": False, "padre": "2120"},
    {"codigo": "2125", "nombre": "Indemnización por Pagar", "tipo": "pasivo", "naturaleza": "acreedora", "nivel": 4, "acepta_tercero": False, "padre": "2120"},
    
    {"codigo": "2130", "nombre": "Impuestos por Pagar", "tipo": "pasivo", "naturaleza": "acreedora", "nivel": 3, "acepta_tercero": False, "padre": "2100"},
    {"codigo": "2131", "nombre": "IVA Débito Fiscal", "tipo": "pasivo", "naturaleza": "acreedora", "nivel": 4, "acepta_tercero": False, "padre": "2130"},
    {"codigo": "2132", "nombre": "ISR por Pagar", "tipo": "pasivo", "naturaleza": "acreedora", "nivel": 4, "acepta_tercero": False, "padre": "2130"},
    {"codigo": "2133", "nombre": "Retenciones ISR por Pagar", "tipo": "pasivo", "naturaleza": "acreedora", "nivel": 4, "acepta_tercero": False, "padre": "2130"},
    {"codigo": "2134", "nombre": "Retenciones IVA por Pagar", "tipo": "pasivo", "naturaleza": "acreedora", "nivel": 4, "acepta_tercero": False, "padre": "2130"},
    {"codigo": "2135", "nombre": "PAT (Impuesto Empresas Mercantiles)", "tipo": "pasivo", "naturaleza": "acreedora", "nivel": 4, "acepta_tercero": False, "padre": "2130"},
    
    {"codigo": "2140", "nombre": "Anticipos de Clientes", "tipo": "pasivo", "naturaleza": "acreedora", "nivel": 3, "acepta_tercero": True, "padre": "2100"},
    
    {"codigo": "2150", "nombre": "Préstamos Bancarios Corto Plazo", "tipo": "pasivo", "naturaleza": "acreedora", "nivel": 3, "acepta_tercero": False, "padre": "2100"},
    
    # Pasivo No Corriente
    {"codigo": "2210", "nombre": "Préstamos Bancarios Largo Plazo", "tipo": "pasivo", "naturaleza": "acreedora", "nivel": 3, "acepta_tercero": False, "padre": "2200"},
    {"codigo": "2220", "nombre": "Hipotecas por Pagar", "tipo": "pasivo", "naturaleza": "acreedora", "nivel": 3, "acepta_tercero": False, "padre": "2200"},
    {"codigo": "2230", "nombre": "Provisiones Largo Plazo", "tipo": "pasivo", "naturaleza": "acreedora", "nivel": 3, "acepta_tercero": False, "padre": "2200"},

    # ============================================================
    # PATRIMONIO (3000-3999)
    # ============================================================
    {"codigo": "3000", "nombre": "PATRIMONIO", "tipo": "patrimonio", "naturaleza": "acreedora", "nivel": 1, "acepta_tercero": False},
    {"codigo": "3100", "nombre": "Capital Social", "tipo": "patrimonio", "naturaleza": "acreedora", "nivel": 2, "acepta_tercero": False, "padre": "3000"},
    {"codigo": "3200", "nombre": "Utilidades Retenidas", "tipo": "patrimonio", "naturaleza": "acreedora", "nivel": 2, "acepta_tercero": False, "padre": "3000"},
    {"codigo": "3300", "nombre": "Utilidad del Ejercicio", "tipo": "patrimonio", "naturaleza": "acreedora", "nivel": 2, "acepta_tercero": False, "padre": "3000"},
    {"codigo": "3400", "nombre": "Reserva Legal", "tipo": "patrimonio", "naturaleza": "acreedora", "nivel": 2, "acepta_tercero": False, "padre": "3000"},
    {"codigo": "3500", "nombre": "Superávit por Revaluación", "tipo": "patrimonio", "naturaleza": "acreedora", "nivel": 2, "acepta_tercero": False, "padre": "3000"},

    # ============================================================
    # INGRESOS (4000-4999)
    # ============================================================
    {"codigo": "4000", "nombre": "INGRESOS", "tipo": "ingreso", "naturaleza": "acreedora", "nivel": 1, "acepta_tercero": False},
    
    {"codigo": "4100", "nombre": "Ingresos por Ventas", "tipo": "ingreso", "naturaleza": "acreedora", "nivel": 2, "acepta_tercero": False, "padre": "4000"},
    {"codigo": "4110", "nombre": "Ventas de Mercaderías", "tipo": "ingreso", "naturaleza": "acreedora", "nivel": 3, "acepta_tercero": False, "padre": "4100"},
    {"codigo": "4120", "nombre": "Ventas de Producto Terminado", "tipo": "ingreso", "naturaleza": "acreedora", "nivel": 3, "acepta_tercero": False, "padre": "4100"},
    {"codigo": "4130", "nombre": "Ventas de Servicios", "tipo": "ingreso", "naturaleza": "acreedora", "nivel": 3, "acepta_tercero": False, "padre": "4100"},
    {"codigo": "4140", "nombre": "Devoluciones sobre Ventas", "tipo": "ingreso", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "4100"},
    {"codigo": "4150", "nombre": "Descuentos sobre Ventas", "tipo": "ingreso", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "4100"},
    
    {"codigo": "4200", "nombre": "Otros Ingresos", "tipo": "ingreso", "naturaleza": "acreedora", "nivel": 2, "acepta_tercero": False, "padre": "4000"},
    {"codigo": "4210", "nombre": "Ingresos Financieros", "tipo": "ingreso", "naturaleza": "acreedora", "nivel": 3, "acepta_tercero": False, "padre": "4200"},
    {"codigo": "4220", "nombre": "Ingresos por Rentas", "tipo": "ingreso", "naturaleza": "acreedora", "nivel": 3, "acepta_tercero": False, "padre": "4200"},
    {"codigo": "4230", "nombre": "Otros Ingresos Operativos", "tipo": "ingreso", "naturaleza": "acreedora", "nivel": 3, "acepta_tercero": False, "padre": "4200"},

    # ============================================================
    # GASTOS (5000-5999)
    # ============================================================
    {"codigo": "5000", "nombre": "GASTOS", "tipo": "gasto", "naturaleza": "deudora", "nivel": 1, "acepta_tercero": False},
    
    # Costo de Ventas / Producción
    {"codigo": "5100", "nombre": "Costo de Ventas", "tipo": "gasto", "naturaleza": "deudora", "nivel": 2, "acepta_tercero": False, "padre": "5000"},
    {"codigo": "5110", "nombre": "Costo de Mercaderías Vendidas", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5100"},
    {"codigo": "5120", "nombre": "Costo de Producto Terminado Vendido", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5100"},
    {"codigo": "5130", "nombre": "Mano de Obra Directa", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5100"},
    
    {"codigo": "5140", "nombre": "Costos Indirectos de Fabricación (CIF)", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5100"},
    {"codigo": "5141", "nombre": "Materiales Indirectos", "tipo": "gasto", "naturaleza": "deudora", "nivel": 4, "acepta_tercero": False, "padre": "5140"},
    {"codigo": "5142", "nombre": "Mano de Obra Indirecta", "tipo": "gasto", "naturaleza": "deudora", "nivel": 4, "acepta_tercero": False, "padre": "5140"},
    {"codigo": "5143", "nombre": "Depreciación Maquinaria Fabril", "tipo": "gasto", "naturaleza": "deudora", "nivel": 4, "acepta_tercero": False, "padre": "5140"},
    {"codigo": "5144", "nombre": "Servicios Básicos Fabril", "tipo": "gasto", "naturaleza": "deudora", "nivel": 4, "acepta_tercero": False, "padre": "5140"},
    {"codigo": "5145", "nombre": "Mantenimiento Fabril", "tipo": "gasto", "naturaleza": "deudora", "nivel": 4, "acepta_tercero": False, "padre": "5140"},
    {"codigo": "5146", "nombre": "Seguros Fabril", "tipo": "gasto", "naturaleza": "deudora", "nivel": 4, "acepta_tercero": False, "padre": "5140"},
    
    # Gastos de Administración
    {"codigo": "5200", "nombre": "Gastos de Administración", "tipo": "gasto", "naturaleza": "deudora", "nivel": 2, "acepta_tercero": False, "padre": "5000"},
    {"codigo": "5210", "nombre": "Sueldos y Salarios Administrativos", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5200"},
    {"codigo": "5220", "nombre": "Aguinaldo Administrativo", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5200"},
    {"codigo": "5230", "nombre": "Bono 14 Administrativo", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5200"},
    {"codigo": "5240", "nombre": "Vacaciones Administrativas", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5200"},
    {"codigo": "5250", "nombre": "Indemnización Administrativa", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5200"},
    {"codigo": "5260", "nombre": "Cuotas Patronales IGSS", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5200"},
    {"codigo": "5270", "nombre": "Cuota IRTRA (Recreación)", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5200"},
    {"codigo": "5280", "nombre": "Cuota INTECAP (Capacitación)", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5200"},
    {"codigo": "5290", "nombre": "Depreciación Mobiliario Oficina", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5200"},
    {"codigo": "5300", "nombre": "Depreciación Equipo Cómputo", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5200"},
    {"codigo": "5310", "nombre": "Alquileres", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5200"},
    {"codigo": "5320", "nombre": "Servicios Básicos (Agua, Luz, Teléfono)", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5200"},
    {"codigo": "5330", "nombre": "Papelería y Útiles de Oficina", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5200"},
    {"codigo": "5340", "nombre": "Teléfono e Internet", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5200"},
    {"codigo": "5350", "nombre": "Seguros Generales", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5200"},
    {"codigo": "5360", "nombre": "Mantenimiento y Reparaciones", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5200"},
    {"codigo": "5370", "nombre": "Gastos Legales y Notariales", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5200"},
    {"codigo": "5380", "nombre": "Honorarios Profesionales", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": True, "padre": "5200"},
    {"codigo": "5390", "nombre": "Publicidad y Propaganda", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5200"},
    {"codigo": "5400", "nombre": "Gastos de Representación", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5200"},
    
    # Gastos de Ventas
    {"codigo": "5500", "nombre": "Gastos de Ventas", "tipo": "gasto", "naturaleza": "deudora", "nivel": 2, "acepta_tercero": False, "padre": "5000"},
    {"codigo": "5510", "nombre": "Sueldos y Comisiones Vendedores", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5500"},
    {"codigo": "5520", "nombre": "Aguinaldo Ventas", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5500"},
    {"codigo": "5530", "nombre": "Bono 14 Ventas", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5500"},
    {"codigo": "5540", "nombre": "Vacaciones Ventas", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5500"},
    {"codigo": "5550", "nombre": "Cuotas Patronales IGSS Ventas", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5500"},
    {"codigo": "5560", "nombre": "Publicidad y Marketing", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5500"},
    {"codigo": "5570", "nombre": "Fletes y Acarreos", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5500"},
    {"codigo": "5580", "nombre": "Depreciación Equipo Transporte", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5500"},
    {"codigo": "5590", "nombre": "Combustible y Lubricantes", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5500"},
    {"codigo": "5600", "nombre": "Gastos de Viaje", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5500"},
    
    # Gastos Financieros
    {"codigo": "5700", "nombre": "Gastos Financieros", "tipo": "gasto", "naturaleza": "deudora", "nivel": 2, "acepta_tercero": False, "padre": "5000"},
    {"codigo": "5710", "nombre": "Intereses Bancarios", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5700"},
    {"codigo": "5720", "nombre": "Comisiones Bancarias", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5700"},
    {"codigo": "5730", "nombre": "Pérdida Cambiaria", "tipo": "gasto", "naturaleza": "deudora", "nivel": 3, "acepta_tercero": False, "padre": "5700"},
]