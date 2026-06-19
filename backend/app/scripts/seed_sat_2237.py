"""
Seed del Formulario SAT-2237 (Declaración Jurativa del IVA)
============================================================

Estructura basada en el formulario oficial SAT-2237 Release 1
Validado contra formulario presentado: Abril 2025

Secciones:
1. Identificación del Contribuyente
2. Período de Imposición
3. Débito Fiscal por Operaciones Locales
4. Operaciones de Exportación y Transferencia
5. Crédito Fiscal por Operaciones Locales
6. Crédito Fiscal por Operaciones de Exportación y Transferencia
7. Determinación del Crédito Fiscal o Impuesto a Pagar
8. Indicadores Comerciales
9. Monto de Operaciones Realizadas (9.1 Conteos, 9.2 Valores)
10. Rectificación
11. Accesorios
12. Contador
13. Códigos
"""

import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.models.global_models import (
    CasillaSat,
    ExclusionCasilla,
    FormularioSat,
    RegimenFiscal,
    RegimenFormularioSat,
    ReglaFiltradoFactura,
    SeccionFormulario,
)


def seed_sat_2237(db: Session):
    """
    Crea el formulario SAT-2237 completo con secciones, casillas,
    reglas de filtrado y exclusiones basado en el formulario oficial.
    """
    
    # =========================================================================
    # 1. FORMULARIO SAT-2237
    # =========================================================================
    formulario = FormularioSat(
        id=uuid.uuid4(),
        codigo='SAT-2237',
        nombre='Declaración Jurativa Mensual del IVA - Régimen General',
        descripcion='Formulario para la declaración mensual del Impuesto al Valor Agregado. Contribuyentes del Régimen General que realizan operaciones locales, de exportación y/o transferencia.',
        version='1.0',
        fecha_vigencia=date(2025, 1, 1),
        frecuencia='MENSUAL',
        created_by=None
    )
    db.add(formulario)
    db.flush()
    
    print(f"✅ Formulario SAT-2237 creado: {formulario.id}")
    
    # =========================================================================
    # 2. SECCIONES
    # =========================================================================
    secciones_data = [
        {'numero': '1', 'titulo': 'Identificación del Contribuyente', 'tipo': 'IDENTIFICACION', 'orden': 1},
        {'numero': '2', 'titulo': 'Período de Imposición', 'tipo': 'PERIODO', 'orden': 2},
        {'numero': '3', 'titulo': 'Débito Fiscal por Operaciones Locales', 'tipo': 'DEBITO_FISCAL', 'orden': 3},
        {'numero': '4', 'titulo': 'Operaciones de Exportación y Transferencia', 'tipo': 'EXPORTACIONES', 'orden': 4, 'requiere_exportador': True},
        {'numero': '5', 'titulo': 'Crédito Fiscal por Operaciones Locales', 'tipo': 'CREDITO_FISCAL', 'orden': 5},
        {'numero': '6', 'titulo': 'Crédito Fiscal por Operaciones de Exportación y Transferencia', 'tipo': 'CREDITO_FISCAL', 'orden': 6, 'requiere_exportador': True},
        {'numero': '7', 'titulo': 'Determinación del Crédito Fiscal o Impuesto a Pagar', 'tipo': 'DETERMINACION', 'orden': 7},
        {'numero': '8', 'titulo': 'Indicadores Comerciales', 'tipo': 'INFORMATIVA', 'orden': 8},
        {'numero': '9', 'titulo': 'Monto de Operaciones Realizadas', 'tipo': 'INFORMATIVA', 'orden': 9},
        {'numero': '10', 'titulo': 'Rectificación', 'tipo': 'RECTIFICACION', 'orden': 10},
        {'numero': '11', 'titulo': 'Accesorios', 'tipo': 'ACCESORIOS', 'orden': 11},
        {'numero': '12', 'titulo': 'Contador', 'tipo': 'INFORMATIVA', 'orden': 12},
        {'numero': '13', 'titulo': 'Códigos', 'tipo': 'INFORMATIVA', 'orden': 13},
    ]
    
    secciones = {}
    for sec_data in secciones_data:
        seccion = SeccionFormulario(
            id=uuid.uuid4(),
            formulario_id=formulario.id,
            numero_seccion=sec_data['numero'],
            titulo=sec_data['titulo'],
            orden=sec_data['orden'],
            tipo_seccion=sec_data['tipo'],
            es_obligatoria=True,
            requiere_exportador=sec_data.get('requiere_exportador', False),
            created_by=None
        )
        db.add(seccion)
        secciones[sec_data['numero']] = seccion
    
    db.flush()
    print(f"✅ {len(secciones)} secciones creadas")
    
    # =========================================================================
    # 3. CASILLAS - SECCIÓN 3: DÉBITO FISCAL POR OPERACIONES LOCALES
    # =========================================================================
    casillas_seccion_3 = [
        {'codigo': 'SAT2237_3_1', 'codigo_visual': '3.1', 'nombre': 'Ventas exentas y servicios exentos', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_exento_gtq', 'formula': None},
        {'codigo': 'SAT2237_3_2', 'codigo_visual': '3.2', 'nombre': 'Ventas de medicamentos genéricos, alternativos y antirretrovirales', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_exento_gtq', 'formula': None},
        {'codigo': 'SAT2237_3_3', 'codigo_visual': '3.3', 'nombre': 'Ventas no afectas realizadas a contribuyentes calificados Decreto 29-89', 'tipo': 'REFERENCIA', 'campo': 'total_gtq', 'formula': None},
        {'codigo': 'SAT2237_3_4', 'codigo_visual': '3.4', 'nombre': 'Ventas de vehículos terrestres (2+ años anteriores)', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_bienes_gtq', 'formula': None},
        {'codigo': 'SAT2237_3_5', 'codigo_visual': '3.5', 'nombre': 'Ventas de vehículos terrestres (año en curso, siguiente o anterior)', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_bienes_gtq', 'formula': None},
        {'codigo': 'SAT2237_3_5_D', 'codigo_visual': '3.5', 'nombre': 'Débito Fiscal vehículos terrestres', 'tipo': 'DEBITO_FISCAL', 'campo': None, 'formula': '{SAT2237_3_5} * 0.12', 'porcentaje': 12.00},
        {'codigo': 'SAT2237_3_6', 'codigo_visual': '3.6', 'nombre': 'Ventas gravadas', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_bienes_gtq', 'formula': None},
        {'codigo': 'SAT2237_3_6_D', 'codigo_visual': '3.6', 'nombre': 'Débito Fiscal ventas gravadas', 'tipo': 'DEBITO_FISCAL', 'campo': None, 'formula': '{SAT2237_3_6} * 0.12', 'porcentaje': 12.00},
        {'codigo': 'SAT2237_3_7', 'codigo_visual': '3.7', 'nombre': 'Servicios gravados', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_servicios_gtq', 'formula': None},
        {'codigo': 'SAT2237_3_7_D', 'codigo_visual': '3.7', 'nombre': 'Débito Fiscal servicios gravados', 'tipo': 'DEBITO_FISCAL', 'campo': None, 'formula': '{SAT2237_3_7} * 0.12', 'porcentaje': 12.00},
        {'codigo': 'SAT2237_3_SUM', 'codigo_visual': '3.SUM', 'nombre': 'Sumatoria de las columnas BASE y DÉBITOS', 'tipo': 'CALCULADO', 'campo': None, 'formula': '{SAT2237_3_1} + {SAT2237_3_2} + {SAT2237_3_4} + {SAT2237_3_5} + {SAT2237_3_6} + {SAT2237_3_7}'},
    ]
    
    # =========================================================================
    # 4. CASILLAS - SECCIÓN 4: OPERACIONES DE EXPORTACIÓN Y TRANSFERENCIA
    # =========================================================================
    casillas_seccion_4 = [
        {'codigo': 'SAT2237_4_1', 'codigo_visual': '4.1', 'nombre': 'Exportaciones a Centro América', 'tipo': 'REFERENCIA', 'campo': 'total_gtq', 'formula': None},
        {'codigo': 'SAT2237_4_2', 'codigo_visual': '4.2', 'nombre': 'Exportaciones al resto del mundo', 'tipo': 'REFERENCIA', 'campo': 'total_gtq', 'formula': None},
        {'codigo': 'SAT2237_4_3', 'codigo_visual': '4.3', 'nombre': 'Transferencias con FYDUCA', 'tipo': 'REFERENCIA', 'campo': 'total_gtq', 'formula': None},
        {'codigo': 'SAT2237_4_4', 'codigo_visual': '4.4', 'nombre': 'Ventas de medicamentos genéricos, alternativos y antirretrovirales', 'tipo': 'REFERENCIA', 'campo': 'total_exento_gtq', 'formula': None},
        {'codigo': 'SAT2237_4_5', 'codigo_visual': '4.5', 'nombre': 'Ventas de vehículos terrestres (2+ años anteriores)', 'tipo': 'REFERENCIA', 'campo': 'total_gtq', 'formula': None},
        {'codigo': 'SAT2237_4_6', 'codigo_visual': '4.6', 'nombre': 'Ventas de vehículos terrestres (año en curso, siguiente o anterior)', 'tipo': 'REFERENCIA', 'campo': 'total_gtq', 'formula': None},
        {'codigo': 'SAT2237_4_SUM', 'codigo_visual': '4.SUM', 'nombre': 'Sumatoria de la columna Operaciones de Exportación y Transferencia', 'tipo': 'CALCULADO', 'campo': None, 'formula': '{SAT2237_4_1} + {SAT2237_4_2} + {SAT2237_4_3} + {SAT2237_4_4} + {SAT2237_4_5} + {SAT2237_4_6}'},
        {'codigo': 'SAT2237_4_7', 'codigo_visual': '4.7', 'nombre': 'Total crédito fiscal recibido Régimen Especial u Optativo (Débito)', 'tipo': 'DEBITO_FISCAL', 'campo': None, 'formula': None},
        {'codigo': 'SAT2237_4_8', 'codigo_visual': '4.8', 'nombre': 'Débito facturas especiales emitidas por exportadores', 'tipo': 'DEBITO_FISCAL', 'campo': None, 'formula': None},
        {'codigo': 'SAT2237_4_TOTAL', 'codigo_visual': '4.TOTAL', 'nombre': 'Total determinación del débito Fiscal', 'tipo': 'CALCULADO', 'campo': None, 'formula': '{SAT2237_4_7} + {SAT2237_4_8}'},
    ]
    
    # =========================================================================
    # 5. CASILLAS - SECCIÓN 5: CRÉDITO FISCAL POR OPERACIONES LOCALES
    # =========================================================================
    casillas_seccion_5 = [
        {'codigo': 'SAT2237_5_1', 'codigo_visual': '5.1', 'nombre': 'Compras de medicamentos genéricos, alternativos y antirretrovirales', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_exento_gtq', 'formula': None},
        {'codigo': 'SAT2237_5_2', 'codigo_visual': '5.2', 'nombre': 'Compras y servicios adquiridos de pequeños contribuyentes', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gtq', 'formula': None},
        {'codigo': 'SAT2237_5_2_C', 'codigo_visual': '5.2', 'nombre': 'Crédito Fiscal pequeños contribuyentes', 'tipo': 'CREDITO_FISCAL', 'campo': None, 'formula': '{SAT2237_5_2} * 0.04', 'porcentaje': 4.00},
        {'codigo': 'SAT2237_5_3', 'codigo_visual': '5.3', 'nombre': 'Compras que no generan derecho a compensación del crédito fiscal', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_gtq', 'formula': None},
        {'codigo': 'SAT2237_5_4', 'codigo_visual': '5.4', 'nombre': 'Compras de vehículos terrestres (2+ años anteriores)', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_bienes_gtq', 'formula': None},
        {'codigo': 'SAT2237_5_5', 'codigo_visual': '5.5', 'nombre': 'Compras de vehículos terrestres (año en curso, siguiente o anterior)', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_bienes_gtq', 'formula': None},
        {'codigo': 'SAT2237_5_5_C', 'codigo_visual': '5.5', 'nombre': 'Crédito Fiscal vehículos terrestres', 'tipo': 'CREDITO_FISCAL', 'campo': None, 'formula': '{SAT2237_5_5} * 0.12', 'porcentaje': 12.00},
        {'codigo': 'SAT2237_5_6', 'codigo_visual': '5.6', 'nombre': 'Compras de combustibles', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_gtq', 'formula': None},
        {'codigo': 'SAT2237_5_6_C', 'codigo_visual': '5.6', 'nombre': 'Crédito Fiscal combustibles', 'tipo': 'CREDITO_FISCAL', 'campo': None, 'formula': '{SAT2237_5_6} * 0.12', 'porcentaje': 12.00},
        {'codigo': 'SAT2237_5_7', 'codigo_visual': '5.7', 'nombre': 'Otras compras', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_bienes_gtq', 'formula': None},
        {'codigo': 'SAT2237_5_7_C', 'codigo_visual': '5.7', 'nombre': 'Crédito Fiscal otras compras', 'tipo': 'CREDITO_FISCAL', 'campo': None, 'formula': '{SAT2237_5_7} * 0.12', 'porcentaje': 12.00},
        {'codigo': 'SAT2237_5_8', 'codigo_visual': '5.8', 'nombre': 'Servicios adquiridos', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_servicios_gtq', 'formula': None},
        {'codigo': 'SAT2237_5_8_C', 'codigo_visual': '5.8', 'nombre': 'Crédito Fiscal servicios adquiridos', 'tipo': 'CREDITO_FISCAL', 'campo': None, 'formula': '{SAT2237_5_8} * 0.12', 'porcentaje': 12.00},
        {'codigo': 'SAT2237_5_9', 'codigo_visual': '5.9', 'nombre': 'Importaciones de Centro América', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_gtq', 'formula': None},
        {'codigo': 'SAT2237_5_9_C', 'codigo_visual': '5.9', 'nombre': 'Crédito Fiscal importaciones Centro América', 'tipo': 'CREDITO_FISCAL', 'campo': None, 'formula': '{SAT2237_5_9} * 0.12', 'porcentaje': 12.00},
        {'codigo': 'SAT2237_5_10', 'codigo_visual': '5.10', 'nombre': 'Adquisiciones con FYDUCA', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_gtq', 'formula': None},
        {'codigo': 'SAT2237_5_10_C', 'codigo_visual': '5.10', 'nombre': 'Crédito Fiscal FYDUCA', 'tipo': 'CREDITO_FISCAL', 'campo': None, 'formula': '{SAT2237_5_10} * 0.12', 'porcentaje': 12.00},
        {'codigo': 'SAT2237_5_11', 'codigo_visual': '5.11', 'nombre': 'Importaciones del resto del mundo', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_gtq', 'formula': None},
        {'codigo': 'SAT2237_5_11_C', 'codigo_visual': '5.11', 'nombre': 'Crédito Fiscal importaciones resto del mundo', 'tipo': 'CREDITO_FISCAL', 'campo': None, 'formula': '{SAT2237_5_11} * 0.12', 'porcentaje': 12.00},
        {'codigo': 'SAT2237_5_12', 'codigo_visual': '5.12', 'nombre': 'Compras de activos fijos directamente vinculados con el proceso productivo', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_gtq', 'formula': None},
        {'codigo': 'SAT2237_5_12_C', 'codigo_visual': '5.12', 'nombre': 'Crédito Fiscal activos fijos', 'tipo': 'CREDITO_FISCAL', 'campo': None, 'formula': '{SAT2237_5_12} * 0.12', 'porcentaje': 12.00},
        {'codigo': 'SAT2237_5_13', 'codigo_visual': '5.13', 'nombre': 'Importaciones de activos fijos directamente vinculados con el proceso productivo', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_gtq', 'formula': None},
        {'codigo': 'SAT2237_5_13_C', 'codigo_visual': '5.13', 'nombre': 'Crédito Fiscal importación activos fijos', 'tipo': 'CREDITO_FISCAL', 'campo': None, 'formula': '{SAT2237_5_13} * 0.12', 'porcentaje': 12.00},
        {'codigo': 'SAT2237_5_14', 'codigo_visual': '5.14', 'nombre': 'IVA conforme constancias de exención recibidas', 'tipo': 'CREDITO_FISCAL', 'campo': None, 'formula': None},
        {'codigo': 'SAT2237_5_REM', 'codigo_visual': '5.REM', 'nombre': 'Remanente de crédito fiscal del período anterior', 'tipo': 'REMANENTE', 'campo': None, 'formula': None, 'es_editable': True},
        {'codigo': 'SAT2237_5_SUM', 'codigo_visual': '5.SUM', 'nombre': 'Sumatoria de las columnas BASE y CRÉDITOS', 'tipo': 'CALCULADO', 'campo': None, 'formula': '{SAT2237_5_2_C} + {SAT2237_5_5_C} + {SAT2237_5_6_C} + {SAT2237_5_7_C} + {SAT2237_5_8_C} + {SAT2237_5_9_C} + {SAT2237_5_10_C} + {SAT2237_5_11_C} + {SAT2237_5_12_C} + {SAT2237_5_13_C} + {SAT2237_5_14} + {SAT2237_5_REM}'},
    ]
    
    # =========================================================================
    # 6. CASILLAS - SECCIÓN 6: CRÉDITO FISCAL EXPORTACIONES
    # =========================================================================
    casillas_seccion_6 = [
        {'codigo': 'SAT2237_6_1', 'codigo_visual': '6.1', 'nombre': 'Compras y servicios adquiridos de pequeño contribuyente', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gtq', 'formula': None},
        {'codigo': 'SAT2237_6_1_C', 'codigo_visual': '6.1', 'nombre': 'Crédito Fiscal pequeño contribuyente', 'tipo': 'CREDITO_FISCAL', 'campo': None, 'formula': '{SAT2237_6_1} * 0.04', 'porcentaje': 4.00},
        {'codigo': 'SAT2237_6_2', 'codigo_visual': '6.2', 'nombre': 'Compras de combustibles', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_gtq', 'formula': None},
        {'codigo': 'SAT2237_6_2_C', 'codigo_visual': '6.2', 'nombre': 'Crédito Fiscal combustibles', 'tipo': 'CREDITO_FISCAL', 'campo': None, 'formula': '{SAT2237_6_2} * 0.12', 'porcentaje': 12.00},
        {'codigo': 'SAT2237_6_3', 'codigo_visual': '6.3', 'nombre': 'Otras compras', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_gtq', 'formula': None},
        {'codigo': 'SAT2237_6_3_C', 'codigo_visual': '6.3', 'nombre': 'Crédito Fiscal otras compras', 'tipo': 'CREDITO_FISCAL', 'campo': None, 'formula': '{SAT2237_6_3} * 0.12', 'porcentaje': 12.00},
        {'codigo': 'SAT2237_6_4', 'codigo_visual': '6.4', 'nombre': 'Servicios adquiridos', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_servicios_gtq', 'formula': None},
        {'codigo': 'SAT2237_6_4_C', 'codigo_visual': '6.4', 'nombre': 'Crédito Fiscal servicios', 'tipo': 'CREDITO_FISCAL', 'campo': None, 'formula': '{SAT2237_6_4} * 0.12', 'porcentaje': 12.00},
        {'codigo': 'SAT2237_6_5', 'codigo_visual': '6.5', 'nombre': 'Importaciones de Centro América', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_gtq', 'formula': None},
        {'codigo': 'SAT2237_6_5_C', 'codigo_visual': '6.5', 'nombre': 'Crédito Fiscal importaciones CA', 'tipo': 'CREDITO_FISCAL', 'campo': None, 'formula': '{SAT2237_6_5} * 0.12', 'porcentaje': 12.00},
        {'codigo': 'SAT2237_6_6', 'codigo_visual': '6.6', 'nombre': 'Adquisiciones con FYDUCA', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_gtq', 'formula': None},
        {'codigo': 'SAT2237_6_6_C', 'codigo_visual': '6.6', 'nombre': 'Crédito Fiscal FYDUCA', 'tipo': 'CREDITO_FISCAL', 'campo': None, 'formula': '{SAT2237_6_6} * 0.12', 'porcentaje': 12.00},
        {'codigo': 'SAT2237_6_7', 'codigo_visual': '6.7', 'nombre': 'Importaciones del resto del mundo', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_gtq', 'formula': None},
        {'codigo': 'SAT2237_6_7_C', 'codigo_visual': '6.7', 'nombre': 'Crédito Fiscal importaciones', 'tipo': 'CREDITO_FISCAL', 'campo': None, 'formula': '{SAT2237_6_7} * 0.12', 'porcentaje': 12.00},
        {'codigo': 'SAT2237_6_8', 'codigo_visual': '6.8', 'nombre': 'Compras de activos fijos directamente vinculados', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_gtq', 'formula': None},
        {'codigo': 'SAT2237_6_8_C', 'codigo_visual': '6.8', 'nombre': 'Crédito Fiscal activos fijos', 'tipo': 'CREDITO_FISCAL', 'campo': None, 'formula': '{SAT2237_6_8} * 0.12', 'porcentaje': 12.00},
        {'codigo': 'SAT2237_6_9', 'codigo_visual': '6.9', 'nombre': 'Importaciones de activos fijos directamente vinculados', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_gtq', 'formula': None},
        {'codigo': 'SAT2237_6_9_C', 'codigo_visual': '6.9', 'nombre': 'Crédito Fiscal importación activos fijos', 'tipo': 'CREDITO_FISCAL', 'campo': None, 'formula': '{SAT2237_6_9} * 0.12', 'porcentaje': 12.00},
        {'codigo': 'SAT2237_6_REM', 'codigo_visual': '6.REM', 'nombre': 'Remanente de crédito fiscal del período anterior por exportaciones', 'tipo': 'REMANENTE', 'campo': None, 'formula': None, 'es_editable': True},
        {'codigo': 'SAT2237_6_10', 'codigo_visual': '6.10', 'nombre': 'Crédito facturas especiales emitidas por exportadores', 'tipo': 'CREDITO_FISCAL', 'campo': None, 'formula': None},
        {'codigo': 'SAT2237_6_RET', 'codigo_visual': '6.RET', 'nombre': '(-) Retenciones practicadas por exportadores Decreto 29-89', 'tipo': 'AJUSTE', 'campo': None, 'formula': None, 'naturaleza': 'RESTA'},
        {'codigo': 'SAT2237_6_SUM', 'codigo_visual': '6.SUM', 'nombre': 'Sumatoria de las columnas BASE y CRÉDITOS', 'tipo': 'CALCULADO', 'campo': None, 'formula': '{SAT2237_6_1_C} + {SAT2237_6_2_C} + {SAT2237_6_3_C} + {SAT2237_6_4_C} + {SAT2237_6_5_C} + {SAT2237_6_6_C} + {SAT2237_6_7_C} + {SAT2237_6_8_C} + {SAT2237_6_9_C} + {SAT2237_6_REM} + {SAT2237_6_10} - {SAT2237_6_RET}'},
        {'codigo': 'SAT2237_6_TOTAL', 'codigo_visual': '6.TOTAL', 'nombre': 'Total determinación del Crédito Fiscal', 'tipo': 'CALCULADO', 'campo': None, 'formula': '{SAT2237_6_SUM}'},
    ]
    
    # =========================================================================
    # 7. CASILLAS - SECCIÓN 7: DETERMINACIÓN DEL IMPUESTO
    # =========================================================================
    casillas_seccion_7 = [
        {'codigo': 'SAT2237_7_1', 'codigo_visual': '7.1', 'nombre': 'Crédito fiscal para el período siguiente por operaciones locales', 'tipo': 'CALCULADO', 'campo': None, 'formula': 'CASE WHEN {SAT2237_5_SUM} > {SAT2237_3_SUM} THEN {SAT2237_5_SUM} - {SAT2237_3_SUM} ELSE 0 END'},
        {'codigo': 'SAT2237_7_2', 'codigo_visual': '7.2', 'nombre': 'Crédito fiscal por operaciones de exportación y/o transferencia', 'tipo': 'CALCULADO', 'campo': None, 'formula': 'CASE WHEN {SAT2237_6_TOTAL} > {SAT2237_4_TOTAL} THEN {SAT2237_6_TOTAL} - {SAT2237_4_TOTAL} ELSE 0 END'},
        {'codigo': 'SAT2237_7_3', 'codigo_visual': '7.3', 'nombre': 'IMPUESTO TOTAL DETERMINADO Operaciones locales', 'tipo': 'CALCULADO', 'campo': None, 'formula': 'CASE WHEN {SAT2237_3_SUM} > {SAT2237_5_SUM} THEN {SAT2237_3_SUM} - {SAT2237_5_SUM} ELSE 0 END'},
        {'codigo': 'SAT2237_7_4', 'codigo_visual': '7.4', 'nombre': 'IMPUESTO TOTAL DETERMINADO Operaciones de exportación y/o transferencia', 'tipo': 'CALCULADO', 'campo': None, 'formula': 'CASE WHEN {SAT2237_4_TOTAL} > {SAT2237_6_TOTAL} THEN {SAT2237_4_TOTAL} - {SAT2237_6_TOTAL} ELSE 0 END'},
        {'codigo': 'SAT2237_7_5', 'codigo_visual': '7.5', 'nombre': 'Crédito fiscal para el período siguiente por operaciones de exportación y/o transferencia', 'tipo': 'CALCULADO', 'campo': None, 'formula': '{SAT2237_7_2}'},
        {'codigo': 'SAT2237_7_SALDO', 'codigo_visual': '7.SALDO', 'nombre': 'SALDO DEL IMPUESTO', 'tipo': 'CALCULADO', 'campo': None, 'formula': '{SAT2237_7_3} + {SAT2237_7_4}'},
        {'codigo': 'SAT2237_7_REM', 'codigo_visual': '7.REM', 'nombre': 'Remanente de retenciones del IVA del período anterior', 'tipo': 'REMANENTE', 'campo': None, 'formula': None, 'es_editable': True},
        {'codigo': 'SAT2237_7_ACRED', 'codigo_visual': '7.ACRED', 'nombre': '(-) Acreditamiento en cuenta bancaria del remanente de retención de IVA', 'tipo': 'AJUSTE', 'campo': None, 'formula': None, 'naturaleza': 'RESTA', 'es_editable': True},
        {'codigo': 'SAT2237_7_REM_PER', 'codigo_visual': '7.REM_PER', 'nombre': '(=) Remanente de retenciones del IVA recibidas en el período', 'tipo': 'CALCULADO', 'campo': None, 'formula': '{SAT2237_7_REM} - {SAT2237_7_ACRED}'},
        {'codigo': 'SAT2237_7_CONST', 'codigo_visual': '7.CONST', 'nombre': '(-) Constancias de retenciones del IVA recibidas en el período a declarar', 'tipo': 'AJUSTE', 'campo': None, 'formula': None, 'naturaleza': 'RESTA', 'es_editable': True},
        {'codigo': 'SAT2237_7_SALDO_RET', 'codigo_visual': '7.SALDO_RET', 'nombre': 'Saldo de retenciones para el período siguiente', 'tipo': 'CALCULADO', 'campo': None, 'formula': '{SAT2237_7_REM_PER} - {SAT2237_7_CONST}'},
        {'codigo': 'SAT2237_7_PAGAR', 'codigo_visual': '7.PAGAR', 'nombre': 'IMPUESTO A PAGAR', 'tipo': 'CALCULADO', 'campo': None, 'formula': '{SAT2237_7_SALDO} - {SAT2237_7_SALDO_RET}'},
    ]
    
    # =========================================================================
    # 8. CASILLAS - SECCIÓN 8: INDICADORES COMERCIALES
    # =========================================================================
    casillas_seccion_8 = [
        {'codigo': 'SAT2237_8_1', 'codigo_visual': '8.1', 'nombre': 'Indicadores comerciales, base débitos menos base créditos', 'tipo': 'CALCULADO', 'campo': None, 'formula': '{SAT2237_3_SUM} - {SAT2237_5_SUM}'},
        {'codigo': 'SAT2237_8_2', 'codigo_visual': '8.2', 'nombre': 'Razón ventas y compras, base débitos dividido base créditos', 'tipo': 'CALCULADO', 'campo': None, 'formula': 'CASE WHEN {SAT2237_5_SUM} > 0 THEN {SAT2237_3_SUM} / {SAT2237_5_SUM} ELSE 0 END'},
    ]
    
    # =========================================================================
    # 9. CASILLAS - SECCIÓN 9: MONTO DE OPERACIONES REALIZADAS
    # =========================================================================
    casillas_seccion_9 = [
        {'codigo': 'SAT2237_9_1_E', 'codigo_visual': '9.1.E', 'nombre': 'Valor de las notas de crédito del período (Emitidos)', 'tipo': 'CONTEO', 'campo': None, 'formula': None},
        {'codigo': 'SAT2237_9_1_R', 'codigo_visual': '9.1.R', 'nombre': 'Valor de las notas de crédito del período (Recibidos)', 'tipo': 'CONTEO', 'campo': None, 'formula': None},
        {'codigo': 'SAT2237_9_2_E', 'codigo_visual': '9.2.E', 'nombre': 'Valor de las notas de débito del período (Emitidos)', 'tipo': 'CONTEO', 'campo': None, 'formula': None},
        {'codigo': 'SAT2237_9_2_R', 'codigo_visual': '9.2.R', 'nombre': 'Valor de las notas de débito del período (Recibidos)', 'tipo': 'CONTEO', 'campo': None, 'formula': None},
        {'codigo': 'SAT2237_9_3_E', 'codigo_visual': '9.3.E', 'nombre': 'Valor de constancias de adquisición de insumos de producción local (Emitidos)', 'tipo': 'CONTEO', 'campo': None, 'formula': None},
        {'codigo': 'SAT2237_9_3_R', 'codigo_visual': '9.3.R', 'nombre': 'Valor de constancias de adquisición de insumos de producción local (Recibidos)', 'tipo': 'CONTEO', 'campo': None, 'formula': None},
    ]
    
    # =========================================================================
    # 10. CASILLAS - SECCIÓN 10: RECTIFICACIÓN
    # =========================================================================
    casillas_seccion_10 = [
        {'codigo': 'SAT2237_10_1', 'codigo_visual': '10.1', 'nombre': 'Número de formulario SAT-2237 que se rectifica', 'tipo': 'REFERENCIA', 'campo': None, 'formula': None, 'es_editable': True},
        {'codigo': 'SAT2237_10_2', 'codigo_visual': '10.2', 'nombre': '(-) Impuesto ingresado con el formulario que se rectifica y anteriores', 'tipo': 'AJUSTE', 'campo': None, 'formula': None, 'naturaleza': 'RESTA', 'es_editable': True},
        {'codigo': 'SAT2237_10_3', 'codigo_visual': '10.3', 'nombre': '(=) Impuesto a pagar', 'tipo': 'CALCULADO', 'campo': None, 'formula': '{SAT2237_7_PAGAR} - {SAT2237_10_2}'},
        {'codigo': 'SAT2237_10_4', 'codigo_visual': '10.4', 'nombre': '(=) Impuesto a favor del contribuyente', 'tipo': 'CALCULADO', 'campo': None, 'formula': 'CASE WHEN {SAT2237_10_2} > {SAT2237_7_PAGAR} THEN {SAT2237_10_2} - {SAT2237_7_PAGAR} ELSE 0 END'},
    ]
    
    # =========================================================================
    # 11. CASILLAS - SECCIÓN 11: ACCESORIOS
    # =========================================================================
    casillas_seccion_11 = [
        {'codigo': 'SAT2237_11_1', 'codigo_visual': '11.1', 'nombre': 'Fecha máxima de pago sin accesorios', 'tipo': 'REFERENCIA', 'campo': None, 'formula': None},
        {'codigo': 'SAT2237_11_2', 'codigo_visual': '11.2', 'nombre': '¿Cuándo pagará este formulario?', 'tipo': 'REFERENCIA', 'campo': None, 'formula': None, 'es_editable': True},
        {'codigo': 'SAT2237_11_3', 'codigo_visual': '11.3', 'nombre': '(+) Multa formal (por presentación extemporánea)', 'tipo': 'AJUSTE', 'campo': None, 'formula': None, 'es_editable': True},
        {'codigo': 'SAT2237_11_4', 'codigo_visual': '11.4', 'nombre': '(+) Multa por omisión', 'tipo': 'AJUSTE', 'campo': None, 'formula': None, 'es_editable': True},
        {'codigo': 'SAT2237_11_5', 'codigo_visual': '11.5', 'nombre': '(+) Multa por rectificación', 'tipo': 'AJUSTE', 'campo': None, 'formula': None, 'es_editable': True},
        {'codigo': 'SAT2237_11_6', 'codigo_visual': '11.6', 'nombre': '(+) Intereses', 'tipo': 'AJUSTE', 'campo': None, 'formula': None, 'es_editable': True},
        {'codigo': 'SAT2237_11_7', 'codigo_visual': '11.7', 'nombre': '(+) Mora', 'tipo': 'AJUSTE', 'campo': None, 'formula': None, 'es_editable': True},
        {'codigo': 'SAT2237_11_SUM', 'codigo_visual': '11.SUM', 'nombre': '(=) Accesorios a Pagar', 'tipo': 'CALCULADO', 'campo': None, 'formula': '{SAT2237_11_3} + {SAT2237_11_4} + {SAT2237_11_5} + {SAT2237_11_6} + {SAT2237_11_7}'},
        {'codigo': 'SAT2237_11_TOTAL', 'codigo_visual': '11.TOTAL', 'nombre': 'TOTAL A PAGAR', 'tipo': 'CALCULADO', 'campo': None, 'formula': '{SAT2237_7_PAGAR} + {SAT2237_11_SUM}'},
    ]
    
    # =========================================================================
    # 12. CASILLAS - SECCIÓN 12: CONTADOR
    # =========================================================================
    casillas_seccion_12 = [
        {'codigo': 'SAT2237_12_1', 'codigo_visual': '12.1', 'nombre': 'NIT del contador responsable de la contabilidad del contribuyente', 'tipo': 'REFERENCIA', 'campo': None, 'formula': None, 'es_editable': True},
    ]
    
    # =========================================================================
    # 13. CASILLAS - SECCIÓN 13: CÓDIGOS
    # =========================================================================
    casillas_seccion_13 = [
        {'codigo': 'SAT2237_13_1', 'codigo_visual': '13.1', 'nombre': 'Código de anexo del detalle de facturas especiales', 'tipo': 'REFERENCIA', 'campo': None, 'formula': None, 'es_editable': True},
        {'codigo': 'SAT2237_13_2', 'codigo_visual': '13.2', 'nombre': 'Código resumen de facturación mensual (CRFM)', 'tipo': 'REFERENCIA', 'campo': None, 'formula': None, 'es_editable': True},
    ]
    
    # =========================================================================
    # CREAR TODAS LAS CASILLAS
    # =========================================================================
    todas_las_casillas = []
    
    def crear_casillas(lista_casillas, seccion_id, seccion_numero):
        casillas_creadas = []
        for i, casilla_data in enumerate(lista_casillas, 1):
            casilla = CasillaSat(
                id=uuid.uuid4(),
                seccion_id=seccion_id,
                formulario_id=formulario.id,
                codigo=casilla_data['codigo'],
                codigo_visual=casilla_data['codigo_visual'],
                nombre=casilla_data['nombre'],
                seccion=seccion_numero,
                orden_seccion=i,
                tipo_casilla=casilla_data['tipo'],
                naturaleza=casilla_data.get('naturaleza'),
                formula_calculo=casilla_data.get('formula'),
                porcentaje_aplicable=casilla_data.get('porcentaje'),
                campo_origen_factura=casilla_data.get('campo'),
                es_editable=casilla_data.get('es_editable', False),
                requiere_justificacion=casilla_data.get('es_editable', False),
                es_visible_usuario=True,
                created_by=None
            )
            db.add(casilla)
            casillas_creadas.append(casilla)
        return casillas_creadas
    
    todas_las_casillas.extend(crear_casillas(casillas_seccion_3, secciones['3'].id, '3'))
    todas_las_casillas.extend(crear_casillas(casillas_seccion_4, secciones['4'].id, '4'))
    todas_las_casillas.extend(crear_casillas(casillas_seccion_5, secciones['5'].id, '5'))
    todas_las_casillas.extend(crear_casillas(casillas_seccion_6, secciones['6'].id, '6'))
    todas_las_casillas.extend(crear_casillas(casillas_seccion_7, secciones['7'].id, '7'))
    todas_las_casillas.extend(crear_casillas(casillas_seccion_8, secciones['8'].id, '8'))
    todas_las_casillas.extend(crear_casillas(casillas_seccion_9, secciones['9'].id, '9'))
    todas_las_casillas.extend(crear_casillas(casillas_seccion_10, secciones['10'].id, '10'))
    todas_las_casillas.extend(crear_casillas(casillas_seccion_11, secciones['11'].id, '11'))
    todas_las_casillas.extend(crear_casillas(casillas_seccion_12, secciones['12'].id, '12'))
    todas_las_casillas.extend(crear_casillas(casillas_seccion_13, secciones['13'].id, '13'))
    
    db.flush()
    print(f"✅ {len(todas_las_casillas)} casillas creadas")
    
    # =========================================================================
    # REGLAS DE FILTRADO DE FACTURAS
    # =========================================================================
    def get_casilla(codigo):
        return next((c for c in todas_las_casillas if c.codigo == codigo), None)
    
    reglas_data = [
        # Sección 3: Débito Fiscal Local
        {'casilla': 'SAT2237_3_1', 'nombre': 'Ventas Exentas', 'criterios': {'tipo_operacion': 'Venta', 'es_exento': True, 'es_exportacion': False}, 'campo': 'total_exento_gtq'},
        {'casilla': 'SAT2237_3_6', 'nombre': 'Ventas de Bienes Gravados', 'criterios': {'tipo_operacion': 'Venta', 'es_exento': False, 'es_exportacion': False, 'bien_o_servicio': 'B'}, 'campo': 'total_gravado_bienes_gtq'},
        {'casilla': 'SAT2237_3_7', 'nombre': 'Ventas de Servicios Gravados', 'criterios': {'tipo_operacion': 'Venta', 'es_exento': False, 'es_exportacion': False, 'bien_o_servicio': 'S'}, 'campo': 'total_gravado_servicios_gtq'},
        
        # Sección 4: Exportaciones
        {'casilla': 'SAT2237_4_1', 'nombre': 'Exportaciones a Centroamérica (excepto Honduras)', 'criterios': {'tipo_operacion': 'Venta', 'es_exportacion': True, 'region': 'CENTROAMERICA', 'pais_destino': {'$ne': 'HND'}}, 'campo': 'total_gtq'},
        {'casilla': 'SAT2237_4_2', 'nombre': 'Exportaciones al resto del mundo', 'criterios': {'tipo_operacion': 'Venta', 'es_exportacion': True, 'region': 'FUERA_CENTROAMERICA'}, 'campo': 'total_gtq'},
        {'casilla': 'SAT2237_4_3', 'nombre': 'Transferencias FYDUCA', 'criterios': {'tipo_operacion': 'Venta', 'tipo_documento': 'FYDUCA'}, 'campo': 'total_gtq'},
        
        # Sección 5: Crédito Fiscal Local
        {'casilla': 'SAT2237_5_6', 'nombre': 'Compras de Combustibles', 'criterios': {'tipo_operacion': 'Compra', 'clasificacion_gasto_sat': 'COMBUSTIBLE'}, 'campo': 'total_gravado_gtq'},
        {'casilla': 'SAT2237_5_7', 'nombre': 'Otras Compras', 'criterios': {'tipo_operacion': 'Compra', 'clasificacion_gasto_sat': 'NORMAL', 'bien_o_servicio': 'B'}, 'campo': 'total_gravado_bienes_gtq'},
        {'casilla': 'SAT2237_5_8', 'nombre': 'Servicios Adquiridos', 'criterios': {'tipo_operacion': 'Compra', 'clasificacion_gasto_sat': 'NORMAL', 'bien_o_servicio': 'S'}, 'campo': 'total_gravado_servicios_gtq'},
        {'casilla': 'SAT2237_5_12', 'nombre': 'Compras de Activos Fijos', 'criterios': {'tipo_operacion': 'Compra', 'clasificacion_gasto_sat': 'ACTIVO_FIJO'}, 'campo': 'total_gravado_gtq'},
    ]
    
    reglas_creadas = 0
    for regla_data in reglas_data:
        casilla = get_casilla(regla_data['casilla'])
        if not casilla:
            print(f"⚠️  Casilla no encontrada: {regla_data['casilla']}")
            continue
        
        regla = ReglaFiltradoFactura(
            id=uuid.uuid4(),
            casilla_id=casilla.id,
            nombre=regla_data['nombre'],
            criterios_json=regla_data['criterios'],
            campo_factura=regla_data['campo'],
            operacion='SUMA',
            orden=1,
            es_activa=True,
            created_by=None
        )
        db.add(regla)
        reglas_creadas += 1
    
    print(f"✅ {reglas_creadas} reglas de filtrado creadas")
    
    # =========================================================================
    # EXCLUSIONES (FYDUCA)
    # =========================================================================
    casilla_4_1 = get_casilla('SAT2237_4_1')
    if casilla_4_1:
        exclusion = ExclusionCasilla(
            id=uuid.uuid4(),
            casilla_id=casilla_4_1.id,
            nombre='Excluir FYDUCA Honduras',
            descripcion='Las transferencias FYDUCA van en casilla 4.3',
            criterios_exclusion_json={'tipo_documento': 'FYDUCA'},
            es_activa=True,
            created_by=None
        )
        db.add(exclusion)
        print("✅ Exclusión FYDUCA creada")
    
    # =========================================================================
    # ASOCIAR CON REGÍMENES
    # =========================================================================
    regimenes_sat_2237 = ['RG_UTILIDADES', 'RG_FEL']
    
    for codigo_regimen in regimenes_sat_2237:
        regimen = db.query(RegimenFiscal).filter(RegimenFiscal.codigo == codigo_regimen).first()
        
        if regimen:
            existente = db.query(RegimenFormularioSat).filter(
                RegimenFormularioSat.regimen_id == regimen.id,
                RegimenFormularioSat.formulario_id == formulario.id
            ).first()
            
            if not existente:
                asociacion = RegimenFormularioSat(
                    id=uuid.uuid4(),
                    regimen_id=regimen.id,
                    formulario_id=formulario.id,
                    es_obligatorio=True,
                    created_by=None
                )
                db.add(asociacion)
                print(f"✅ SAT-2237 asociado a régimen {codigo_regimen}")
    
    # =========================================================================
    # COMMIT FINAL
    # =========================================================================
    db.commit()
    
    print("\n" + "="*70)
    print("✅ SEED SAT-2237 COMPLETADO EXITOSAMENTE")
    print("="*70)
    print(f"Formulario: {formulario.codigo}")
    print(f"Secciones: {len(secciones)}")
    print(f"Casillas: {len(todas_las_casillas)}")
    print(f"Reglas de filtrado: {reglas_creadas}")
    print("Exclusiones: 1 (FYDUCA)")
    print("="*70)
    
    return formulario


if __name__ == "__main__":
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        seed_sat_2237(db)
        print("\n🎉 Seed ejecutado correctamente")
    except Exception as e:
        db.rollback()
        print(f"❌ Error ejecutando seed: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()