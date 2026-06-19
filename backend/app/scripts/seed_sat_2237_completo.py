"""
Seed completo del Formulario SAT-2237 con versionado (Versión Asíncrona)
=========================================================================

Crea dos versiones:
- v1.0 (2025): Formulario oficial de abril 2025
- v2.0 (2026): Con secciones 9.1 y 9.2 separadas

Basado en el formulario real: Formulario46992039616-abril-2025.pdf
"""

import os
import sys
import traceback
import uuid
from datetime import date

# Configurar PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


async def seed_sat_2237_completo(db):
    """
    Crea el SAT-2237 completo con versionado v1.0 (2025) y v2.0 (2026)
    """
    
    from app.models.global_models import (
        CasillaSat,
        ExclusionCasilla,
        FormularioSat,
        RegimenFiscal,
        RegimenFormularioSat,
        ReglaFiltradoFactura,
        SeccionFormulario,
    )
    
    print("="*70)
    print("INICIANDO SEED SAT-2237 CON VERSIONADO (ASÍNCRONO)")
    print("="*70)
    
    # =========================================================================
    # VERSIÓN 1.0 (2025) - Formulario oficial abril 2025
    # =========================================================================
    print("\n📋 Creando SAT-2237 v1.0 (2025)...")
    
    formulario_v1 = FormularioSat(
        id=uuid.uuid4(),
        codigo='SAT-2237',
        version='1.0',
        nombre='Declaración Jurativa Mensual del IVA - Régimen General',
        descripcion='IVA GENERAL SAT-2237 Release 1. Contribuyentes que realizan operaciones locales, de exportación y/o transferencia.',
        fecha_vigencia_desde=date(2025, 1, 1),
        fecha_vigencia_hasta=date(2025, 12, 31),
        es_version_activa=False,
        created_by=None
    )
    db.add(formulario_v1)
    await db.flush()
    
    print(f"✅ Formulario v1.0 creado: {formulario_v1.id}")
    
    # =========================================================================
    # SECCIONES v1.0
    # =========================================================================
    secciones_v1_data = [
        {'numero': '1', 'titulo': 'NIT DEL CONTRIBUYENTE', 'tipo': 'IDENTIFICACION', 'orden': 1},
        {'numero': '2', 'titulo': 'PERÍODO DE IMPOSICIÓN', 'tipo': 'PERIODO', 'orden': 2},
        {'numero': '3', 'titulo': 'DÉBITO FISCAL POR OPERACIONES LOCALES', 'tipo': 'DEBITO_FISCAL', 'orden': 3},
        {'numero': '4', 'titulo': 'OPERACIONES DE EXPORTACIÓN Y TRANSFERENCIA', 'tipo': 'EXPORTACIONES', 'orden': 4, 'requiere_exportador': True},
        {'numero': '5', 'titulo': 'CRÉDITO FISCAL POR OPERACIONES LOCALES', 'tipo': 'CREDITO_FISCAL', 'orden': 5},
        {'numero': '6', 'titulo': 'CRÉDITO FISCAL POR OPERACIONES DE EXPORTACIÓN Y TRANSFERENCIA', 'tipo': 'CREDITO_FISCAL', 'orden': 6, 'requiere_exportador': True},
        {'numero': '7', 'titulo': 'DETERMINACIÓN DEL CRÉDITO FISCAL O IMPUESTO A PAGAR', 'tipo': 'DETERMINACION', 'orden': 7},
        {'numero': '8', 'titulo': 'INDICADORES COMERCIALES', 'tipo': 'INFORMATIVA', 'orden': 8},
        {'numero': '9', 'titulo': 'MONTO DE OPERACIONES REALIZADAS', 'tipo': 'INFORMATIVA', 'orden': 9},
        {'numero': '10', 'titulo': 'RECTIFICACIÓN', 'tipo': 'RECTIFICACION', 'orden': 10},
        {'numero': '11', 'titulo': 'ACCESORIOS', 'tipo': 'ACCESORIOS', 'orden': 11},
        {'numero': '12', 'titulo': 'CONTADOR', 'tipo': 'INFORMATIVA', 'orden': 12},
        {'numero': '13', 'titulo': 'CÓDIGOS', 'tipo': 'INFORMATIVA', 'orden': 13},
    ]
    
    secciones_v1 = {}
    for sec_data in secciones_v1_data:
        seccion = SeccionFormulario(
            id=uuid.uuid4(),
            formulario_id=formulario_v1.id,
            numero_seccion=sec_data['numero'],
            titulo=sec_data['titulo'],
            orden=sec_data['orden'],
            tipo_seccion=sec_data['tipo'],
            es_obligatoria=True,
            requiere_exportador=sec_data.get('requiere_exportador', False),
            created_by=None
        )
        db.add(seccion)
        secciones_v1[sec_data['numero']] = seccion
    
    await db.flush()
    print(f"✅ {len(secciones_v1)} secciones v1.0 creadas")
    
    # =========================================================================
    # CASILLAS v1.0 - SECCIÓN 3: DÉBITO FISCAL LOCAL
    # =========================================================================
    casillas_seccion_3_v1 = [
        {'codigo': '3.1', 'nombre': 'Ventas exentas y servicios exentos', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_exento_gtq'},
        {'codigo': '3.2', 'nombre': 'Ventas de medicamentos genéricos, alternativos y antirretrovirales', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_exento_gtq'},
        {'codigo': '3.3', 'nombre': 'Ventas no afectas realizadas a contribuyentes calificados con el Decreto No. 29-89 y sus reformas', 'tipo': 'REFERENCIA', 'campo': 'total_gtq'},
        {'codigo': '3.4', 'nombre': 'Ventas de vehículos terrestres del modelo de dos años o más anteriores al del año en curso', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_bienes_gtq'},
        {'codigo': '3.5', 'nombre': 'Ventas de vehículos terrestres del modelo del año en curso, del año siguiente o anterior al del año en curso', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_bienes_gtq'},
        {'codigo': '3.5_D', 'nombre': 'Débito Fiscal vehículos terrestres (año en curso)', 'tipo': 'DEBITO_FISCAL', 'formula': '{3.5} * 0.12', 'porcentaje': 12.00},
        {'codigo': '3.6', 'nombre': 'Ventas gravadas', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_bienes_gtq'},
        {'codigo': '3.6_D', 'nombre': 'Débito Fiscal ventas gravadas', 'tipo': 'DEBITO_FISCAL', 'formula': '{3.6} * 0.12', 'porcentaje': 12.00},
        {'codigo': '3.7', 'nombre': 'Servicios gravados', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_servicios_gtq'},
        {'codigo': '3.7_D', 'nombre': 'Débito Fiscal servicios gravados', 'tipo': 'DEBITO_FISCAL', 'formula': '{3.7} * 0.12', 'porcentaje': 12.00},
        {'codigo': '3_SUM', 'nombre': 'Sumatoria de las columnas BASE y DÉBITOS', 'tipo': 'CALCULADO', 'formula': '{3.1} + {3.2} + {3.4} + {3.5} + {3.6} + {3.7}'},
    ]
    
    # =========================================================================
    # CASILLAS v1.0 - SECCIÓN 4: EXPORTACIONES
    # =========================================================================
    casillas_seccion_4_v1 = [
        {'codigo': '4.1', 'nombre': 'Exportaciones a Centro América', 'tipo': 'REFERENCIA', 'campo': 'total_gtq'},
        {'codigo': '4.2', 'nombre': 'Exportaciones al resto del mundo', 'tipo': 'REFERENCIA', 'campo': 'total_gtq'},
        {'codigo': '4.3', 'nombre': 'Transferencias con FYDUCA', 'tipo': 'REFERENCIA', 'campo': 'total_gtq'},
        {'codigo': '4.4', 'nombre': 'Ventas de medicamentos genéricos, alternativos y antirretrovirales', 'tipo': 'REFERENCIA', 'campo': 'total_exento_gtq'},
        {'codigo': '4.5', 'nombre': 'Ventas de vehículos terrestres del modelo de dos años o más anteriores al del año en curso', 'tipo': 'REFERENCIA', 'campo': 'total_gtq'},
        {'codigo': '4.6', 'nombre': 'Ventas de vehículos terrestres del modelo del año en curso, del año siguiente o anterior al del año en curso', 'tipo': 'REFERENCIA', 'campo': 'total_gtq'},
        {'codigo': '4_SUM', 'nombre': 'Sumatoria de la columna Operaciones de Exportación y Transferencia', 'tipo': 'CALCULADO', 'formula': '{4.1} + {4.2} + {4.3} + {4.4} + {4.5} + {4.6}'},
        {'codigo': '4.7', 'nombre': 'Total crédito fiscal recibido Régimen Especial u Optativo de Devolución de Crédito Fiscal a los Exportadores y Transferentes (Débito)', 'tipo': 'DEBITO_FISCAL', 'es_editable': True},
        {'codigo': '4.8', 'nombre': 'Débito facturas especiales emitidas por exportadores registrados en Régimen Especial u Optativo de Devolución de Crédito Fiscal a los Exportadores o por exportadores agropecuarios, artesanales y productos reciclados (Débito)', 'tipo': 'DEBITO_FISCAL', 'es_editable': True},
        {'codigo': '4_TOTAL', 'nombre': 'Total determinación del débito Fiscal', 'tipo': 'CALCULADO', 'formula': '{4.7} + {4.8}'},
    ]
    
    # =========================================================================
    # CASILLAS v1.0 - SECCIÓN 5: CRÉDITO FISCAL LOCAL
    # =========================================================================
    casillas_seccion_5_v1 = [
        {'codigo': '5.1', 'nombre': 'Compras de medicamentos genéricos, alternativos y antirretrovirales', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_exento_gtq'},
        {'codigo': '5.2', 'nombre': 'Compras y servicios adquiridos de pequeños contribuyentes', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gtq'},
        {'codigo': '5.2_C', 'nombre': 'Crédito Fiscal pequeños contribuyentes', 'tipo': 'CREDITO_FISCAL', 'formula': '{5.2} * 0.04', 'porcentaje': 4.00},
        {'codigo': '5.3', 'nombre': 'Compras que no generan derecho a compensación del crédito fiscal', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_gtq'},
        {'codigo': '5.4', 'nombre': 'Compras de vehículos terrestres del modelo de dos años o más anteriores al del año en curso', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_bienes_gtq'},
        {'codigo': '5.4_C', 'nombre': 'Crédito Fiscal vehículos terrestres (2+ años)', 'tipo': 'CREDITO_FISCAL', 'formula': '{5.4} * 0.12', 'porcentaje': 12.00},
        {'codigo': '5.5', 'nombre': 'Compras de vehículos terrestres del modelo del año en curso, del año siguiente o anterior al del año en curso', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_bienes_gtq'},
        {'codigo': '5.5_C', 'nombre': 'Crédito Fiscal vehículos terrestres (año en curso)', 'tipo': 'CREDITO_FISCAL', 'formula': '{5.5} * 0.12', 'porcentaje': 12.00},
        {'codigo': '5.6', 'nombre': 'Compras de combustibles', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_gtq'},
        {'codigo': '5.6_C', 'nombre': 'Crédito Fiscal combustibles', 'tipo': 'CREDITO_FISCAL', 'formula': '{5.6} * 0.12', 'porcentaje': 12.00},
        {'codigo': '5.7', 'nombre': 'Otras compras', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_bienes_gtq'},
        {'codigo': '5.7_C', 'nombre': 'Crédito Fiscal otras compras', 'tipo': 'CREDITO_FISCAL', 'formula': '{5.7} * 0.12', 'porcentaje': 12.00},
        {'codigo': '5.8', 'nombre': 'Servicios adquiridos', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_servicios_gtq'},
        {'codigo': '5.8_C', 'nombre': 'Crédito Fiscal servicios adquiridos', 'tipo': 'CREDITO_FISCAL', 'formula': '{5.8} * 0.12', 'porcentaje': 12.00},
        {'codigo': '5.9', 'nombre': 'Importaciones de Centro América', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_gtq'},
        {'codigo': '5.9_C', 'nombre': 'Crédito Fiscal importaciones Centro América', 'tipo': 'CREDITO_FISCAL', 'formula': '{5.9} * 0.12', 'porcentaje': 12.00},
        {'codigo': '5.10', 'nombre': 'Adquisiciones con FYDUCA', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_gtq'},
        {'codigo': '5.10_C', 'nombre': 'Crédito Fiscal FYDUCA', 'tipo': 'CREDITO_FISCAL', 'formula': '{5.10} * 0.12', 'porcentaje': 12.00},
        {'codigo': '5.11', 'nombre': 'Importaciones del resto del mundo', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_gtq'},
        {'codigo': '5.11_C', 'nombre': 'Crédito Fiscal importaciones resto del mundo', 'tipo': 'CREDITO_FISCAL', 'formula': '{5.11} * 0.12', 'porcentaje': 12.00},
        {'codigo': '5.12', 'nombre': 'Compras de activos fijos directamente vinculados con el proceso productivo', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_gtq'},
        {'codigo': '5.12_C', 'nombre': 'Crédito Fiscal activos fijos', 'tipo': 'CREDITO_FISCAL', 'formula': '{5.12} * 0.12', 'porcentaje': 12.00},
        {'codigo': '5.13', 'nombre': 'Importaciones de activos fijos directamente vinculados con el proceso productivo', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_gtq'},
        {'codigo': '5.13_C', 'nombre': 'Crédito Fiscal importación activos fijos', 'tipo': 'CREDITO_FISCAL', 'formula': '{5.13} * 0.12', 'porcentaje': 12.00},
        {'codigo': '5.14', 'nombre': 'IVA conforme constancias de exención recibidas', 'tipo': 'CREDITO_FISCAL', 'es_editable': True},
        {'codigo': '5.15', 'nombre': 'Remanente de crédito fiscal del período anterior', 'tipo': 'REMANENTE', 'es_editable': True},
        {'codigo': '5_SUM', 'nombre': 'Sumatoria de las columnas BASE y CRÉDITOS', 'tipo': 'CALCULADO', 'formula': '{5.2_C} + {5.4_C} + {5.5_C} + {5.6_C} + {5.7_C} + {5.8_C} + {5.9_C} + {5.10_C} + {5.11_C} + {5.12_C} + {5.13_C} + {5.14} + {5.15}'},
    ]
    
    # =========================================================================
    # CASILLAS v1.0 - SECCIÓN 6: CRÉDITO FISCAL EXPORTACIONES
    # =========================================================================
    casillas_seccion_6_v1 = [
        {'codigo': '6.1', 'nombre': 'Compras y servicios adquiridos de pequeño contribuyente', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gtq'},
        {'codigo': '6.1_C', 'nombre': 'Crédito Fiscal pequeño contribuyente', 'tipo': 'CREDITO_FISCAL', 'formula': '{6.1} * 0.04', 'porcentaje': 4.00},
        {'codigo': '6.2', 'nombre': 'Compras de combustibles', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_gtq'},
        {'codigo': '6.2_C', 'nombre': 'Crédito Fiscal combustibles', 'tipo': 'CREDITO_FISCAL', 'formula': '{6.2} * 0.12', 'porcentaje': 12.00},
        {'codigo': '6.3', 'nombre': 'Otras compras', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_gtq'},
        {'codigo': '6.3_C', 'nombre': 'Crédito Fiscal otras compras', 'tipo': 'CREDITO_FISCAL', 'formula': '{6.3} * 0.12', 'porcentaje': 12.00},
        {'codigo': '6.4', 'nombre': 'Servicios adquiridos', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_servicios_gtq'},
        {'codigo': '6.4_C', 'nombre': 'Crédito Fiscal servicios', 'tipo': 'CREDITO_FISCAL', 'formula': '{6.4} * 0.12', 'porcentaje': 12.00},
        {'codigo': '6.5', 'nombre': 'Importaciones de Centro América', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_gtq'},
        {'codigo': '6.5_C', 'nombre': 'Crédito Fiscal importaciones CA', 'tipo': 'CREDITO_FISCAL', 'formula': '{6.5} * 0.12', 'porcentaje': 12.00},
        {'codigo': '6.6', 'nombre': 'Adquisiciones con FYDUCA', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_gtq'},
        {'codigo': '6.6_C', 'nombre': 'Crédito Fiscal FYDUCA', 'tipo': 'CREDITO_FISCAL', 'formula': '{6.6} * 0.12', 'porcentaje': 12.00},
        {'codigo': '6.7', 'nombre': 'Importaciones del resto del mundo', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_gtq'},
        {'codigo': '6.7_C', 'nombre': 'Crédito Fiscal importaciones', 'tipo': 'CREDITO_FISCAL', 'formula': '{6.7} * 0.12', 'porcentaje': 12.00},
        {'codigo': '6.8', 'nombre': 'Compras de activos fijos directamente vinculados con el proceso productivo', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_gtq'},
        {'codigo': '6.8_C', 'nombre': 'Crédito Fiscal activos fijos', 'tipo': 'CREDITO_FISCAL', 'formula': '{6.8} * 0.12', 'porcentaje': 12.00},
        {'codigo': '6.9', 'nombre': 'Importaciones de activos fijos directamente vinculados con el proceso productivo', 'tipo': 'BASE_IMPONIBLE', 'campo': 'total_gravado_gtq'},
        {'codigo': '6.9_C', 'nombre': 'Crédito Fiscal importación activos fijos', 'tipo': 'CREDITO_FISCAL', 'formula': '{6.9} * 0.12', 'porcentaje': 12.00},
        {'codigo': '6.10', 'nombre': 'Remanente de crédito fiscal del período anterior por exportaciones', 'tipo': 'REMANENTE', 'es_editable': True},
        {'codigo': '6.11', 'nombre': 'Crédito facturas especiales emitidas por exportadores registrados en Régimen Especial u Optativo de Devolución de Crédito Fiscal a los Exportadores o por exportadores agropecuarios, artesanales y productos reciclados', 'tipo': 'CREDITO_FISCAL', 'es_editable': True},
        {'codigo': '6.12', 'nombre': '(-) Retenciones practicadas por exportadores incluyendo los Decreto No. 29-89', 'tipo': 'AJUSTE', 'naturaleza': 'RESTA', 'es_editable': True},
        {'codigo': '6_SUM', 'nombre': 'Sumatoria de las columnas BASE y CRÉDITOS', 'tipo': 'CALCULADO', 'formula': '{6.1_C} + {6.2_C} + {6.3_C} + {6.4_C} + {6.5_C} + {6.6_C} + {6.7_C} + {6.8_C} + {6.9_C} + {6.10} + {6.11} - {6.12}'},
        {'codigo': '6_TOTAL', 'nombre': 'Total determinación del Crédito Fiscal', 'tipo': 'CALCULADO', 'formula': '{6_SUM}'},
    ]
    
    # =========================================================================
    # CASILLAS v1.0 - SECCIÓN 7: DETERMINACIÓN
    # =========================================================================
    casillas_seccion_7_v1 = [
        {'codigo': '7.1', 'nombre': 'Crédito fiscal para el período siguiente por operaciones locales (Créditos mayor que Débitos)', 'tipo': 'CALCULADO', 'formula': 'CASE WHEN {5_SUM} > {3_SUM} THEN {5_SUM} - {3_SUM} ELSE 0 END'},
        {'codigo': '7.2', 'nombre': 'Crédito fiscal por operaciones de exportación y/o transferencia (Créditos mayor que Débitos)', 'tipo': 'CALCULADO', 'formula': 'CASE WHEN {6_TOTAL} > {4_TOTAL} THEN {6_TOTAL} - {4_TOTAL} ELSE 0 END'},
        {'codigo': '7.3', 'nombre': 'IMPUESTO TOTAL DETERMINADO (Débitos mayor que Créditos) Operaciones locales', 'tipo': 'CALCULADO', 'formula': 'CASE WHEN {3_SUM} > {5_SUM} THEN {3_SUM} - {5_SUM} ELSE 0 END'},
        {'codigo': '7.4', 'nombre': 'IMPUESTO TOTAL DETERMINADO (Débitos mayor que Créditos) Operaciones de exportación y/o transferencia', 'tipo': 'CALCULADO', 'formula': 'CASE WHEN {4_TOTAL} > {6_TOTAL} THEN {4_TOTAL} - {6_TOTAL} ELSE 0 END'},
        {'codigo': '7.5', 'nombre': 'Crédito fiscal para el período siguiente por operaciones de exportación y/o transferencia', 'tipo': 'CALCULADO', 'formula': '{7.2}'},
        {'codigo': '7_SALDO', 'nombre': 'SALDO DEL IMPUESTO', 'tipo': 'CALCULADO', 'formula': '{7.3} + {7.4}'},
        {'codigo': '7.6', 'nombre': 'Remanente de retenciones del IVA del período anterior', 'tipo': 'REMANENTE', 'es_editable': True},
        {'codigo': '7.7', 'nombre': '(-) Acreditamiento en cuenta bancaria del remanente de retención de IVA', 'tipo': 'AJUSTE', 'naturaleza': 'RESTA', 'es_editable': True},
        {'codigo': '7.8', 'nombre': '(=) Remanente de retenciones del IVA recibidas en el período', 'tipo': 'CALCULADO', 'formula': '{7.6} - {7.7}'},
        {'codigo': '7.9', 'nombre': '(-) Constancias de retenciones del IVA recibidas en el período a declarar', 'tipo': 'AJUSTE', 'naturaleza': 'RESTA', 'es_editable': True},
        {'codigo': '7.10', 'nombre': 'Saldo de retenciones para el período siguiente', 'tipo': 'CALCULADO', 'formula': '{7.8} - {7.9}'},
        {'codigo': '7_PAGAR', 'nombre': 'IMPUESTO A PAGAR', 'tipo': 'CALCULADO', 'formula': '{7_SALDO} - {7.10}'},
    ]
    
    # =========================================================================
    # CASILLAS v1.0 - SECCIÓN 8: INDICADORES COMERCIALES
    # =========================================================================
    casillas_seccion_8_v1 = [
        {'codigo': '8.1', 'nombre': 'Indicadores comerciales, base débitos menos base créditos', 'tipo': 'CALCULADO', 'formula': '{3_SUM} - {5_SUM}'},
        {'codigo': '8.2', 'nombre': 'Razón ventas y compras, base débitos dividido base créditos', 'tipo': 'CALCULADO', 'formula': 'CASE WHEN {5_SUM} > 0 THEN {3_SUM} / {5_SUM} ELSE 0 END'},
    ]
    
    # =========================================================================
    # CASILLAS v1.0 - SECCIÓN 9: MONTO DE OPERACIONES (unificada)
    # =========================================================================
    casillas_seccion_9_v1 = [
        {'codigo': '9.1', 'nombre': 'Valor de las notas de crédito del período', 'tipo': 'REFERENCIA', 'es_editable': True},
        {'codigo': '9.2', 'nombre': 'Valor de las notas de débito del período', 'tipo': 'REFERENCIA', 'es_editable': True},
        {'codigo': '9.3', 'nombre': 'Valor de constancias de adquisición de insumos de producción local', 'tipo': 'REFERENCIA', 'es_editable': True},
    ]
    
    # =========================================================================
    # CASILLAS v1.0 - SECCIONES 10, 11, 12, 13
    # =========================================================================
    casillas_seccion_10_v1 = [
        {'codigo': '10.1', 'nombre': 'Número de formulario SAT-2237 que se rectifica', 'tipo': 'REFERENCIA', 'es_editable': True},
        {'codigo': '10.2', 'nombre': '(-) Impuesto ingresado con el formulario que se rectifica y anteriores', 'tipo': 'AJUSTE', 'naturaleza': 'RESTA', 'es_editable': True},
        {'codigo': '10.3', 'nombre': '(=) Impuesto a pagar', 'tipo': 'CALCULADO', 'formula': '{7_PAGAR} - {10.2}'},
        {'codigo': '10.4', 'nombre': '(=) Impuesto a favor del contribuyente', 'tipo': 'CALCULADO', 'formula': 'CASE WHEN {10.2} > {7_PAGAR} THEN {10.2} - {7_PAGAR} ELSE 0 END'},
    ]
    
    casillas_seccion_11_v1 = [
        {'codigo': '11.1', 'nombre': 'Fecha máxima de pago sin accesorios', 'tipo': 'REFERENCIA'},
        {'codigo': '11.2', 'nombre': '¿Cuándo presentará esta declaración?', 'tipo': 'REFERENCIA', 'es_editable': True},
        {'codigo': '11.3', 'nombre': '(+) Multa formal (por presentación extemporánea)', 'tipo': 'AJUSTE', 'es_editable': True},
        {'codigo': '11.4', 'nombre': '(+) Multa por omisión', 'tipo': 'AJUSTE', 'es_editable': True},
        {'codigo': '11.5', 'nombre': '(+) Multa por rectificación', 'tipo': 'AJUSTE', 'es_editable': True},
        {'codigo': '11.6', 'nombre': '(+) Intereses', 'tipo': 'AJUSTE', 'es_editable': True},
        {'codigo': '11.7', 'nombre': '(+) Mora', 'tipo': 'AJUSTE', 'es_editable': True},
        {'codigo': '11_SUM', 'nombre': '(=) Accesorios a pagar', 'tipo': 'CALCULADO', 'formula': '{11.3} + {11.4} + {11.5} + {11.6} + {11.7}'},
        {'codigo': '11_TOTAL', 'nombre': 'TOTAL A PAGAR', 'tipo': 'CALCULADO', 'formula': '{7_PAGAR} + {11_SUM}'},
    ]
    
    casillas_seccion_12_v1 = [
        {'codigo': '12.1', 'nombre': 'NIT del contador responsable de la contabilidad del contribuyente', 'tipo': 'REFERENCIA', 'es_editable': True},
    ]
    
    casillas_seccion_13_v1 = [
        {'codigo': '13.1', 'nombre': 'Ingrese el código de anexo del detalle de facturas especiales', 'tipo': 'REFERENCIA', 'es_editable': True},
        {'codigo': '13.2', 'nombre': 'Ingrese el código resumen de facturación mensual (CRFM)', 'tipo': 'REFERENCIA', 'es_editable': True},
    ]
    
    # =========================================================================
    # CREAR TODAS LAS CASILLAS v1.0
    # =========================================================================
    def crear_casillas(lista_casillas, seccion_id, seccion_numero):
        casillas_creadas = []
        for i, casilla_data in enumerate(lista_casillas, 1):
            casilla = CasillaSat(
                id=uuid.uuid4(),
                seccion_id=seccion_id,
                formulario_id=formulario_v1.id,
                codigo=casilla_data['codigo'],
                codigo_visual=casilla_data['codigo'],
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
    
    todas_casillas_v1 = []
    todas_casillas_v1.extend(crear_casillas(casillas_seccion_3_v1, secciones_v1['3'].id, '3'))
    todas_casillas_v1.extend(crear_casillas(casillas_seccion_4_v1, secciones_v1['4'].id, '4'))
    todas_casillas_v1.extend(crear_casillas(casillas_seccion_5_v1, secciones_v1['5'].id, '5'))
    todas_casillas_v1.extend(crear_casillas(casillas_seccion_6_v1, secciones_v1['6'].id, '6'))
    todas_casillas_v1.extend(crear_casillas(casillas_seccion_7_v1, secciones_v1['7'].id, '7'))
    todas_casillas_v1.extend(crear_casillas(casillas_seccion_8_v1, secciones_v1['8'].id, '8'))
    todas_casillas_v1.extend(crear_casillas(casillas_seccion_9_v1, secciones_v1['9'].id, '9'))
    todas_casillas_v1.extend(crear_casillas(casillas_seccion_10_v1, secciones_v1['10'].id, '10'))
    todas_casillas_v1.extend(crear_casillas(casillas_seccion_11_v1, secciones_v1['11'].id, '11'))
    todas_casillas_v1.extend(crear_casillas(casillas_seccion_12_v1, secciones_v1['12'].id, '12'))
    todas_casillas_v1.extend(crear_casillas(casillas_seccion_13_v1, secciones_v1['13'].id, '13'))
    
    await db.flush()
    print(f"✅ {len(todas_casillas_v1)} casillas v1.0 creadas")
    
    # =========================================================================
    # VERSIÓN 2.0 (2026) - Duplicar desde v1.0
    # =========================================================================
    print("\n📋 Creando SAT-2237 v2.0 (2026) desde v1.0...")
    
    formulario_v2 = FormularioSat(
        id=uuid.uuid4(),
        codigo='SAT-2237',
        version='2.0',
        nombre='Declaración Jurativa Mensual del IVA - Régimen General',
        descripcion='IVA GENERAL SAT-2237 Release 2. Contribuyentes que realizan operaciones locales, de exportación y/o transferencia. Incluye secciones 9.1 y 9.2 separadas.',
        fecha_vigencia_desde=date(2026, 1, 1),
        fecha_vigencia_hasta=None,
        es_version_activa=True,
        formulario_padre_id=formulario_v1.id,
        created_by=None
    )
    db.add(formulario_v2)
    await db.flush()
    
    # Duplicar secciones de v1.0 a v2.0
    secciones_v2 = {}
    for sec_numero, seccion_v1 in secciones_v1.items():
        seccion_v2 = SeccionFormulario(
            id=uuid.uuid4(),
            formulario_id=formulario_v2.id,
            numero_seccion=seccion_v1.numero_seccion,
            titulo=seccion_v1.titulo,
            descripcion=seccion_v1.descripcion,
            orden=seccion_v1.orden,
            tipo_seccion=seccion_v1.tipo_seccion,
            es_obligatoria=seccion_v1.es_obligatoria,
            requiere_exportador=seccion_v1.requiere_exportador,
            created_by=None
        )
        db.add(seccion_v2)
        secciones_v2[sec_numero] = seccion_v2
    
    # Agregar secciones 9.1 y 9.2 (nuevas en v2.0)
    seccion_9_1 = SeccionFormulario(
        id=uuid.uuid4(),
        formulario_id=formulario_v2.id,
        numero_seccion='9.1',
        titulo='CANTIDAD DE OPERACIONES REALIZADAS',
        descripcion='Conteo de documentos emitidos y recibidos',
        orden=9,
        tipo_seccion='INFORMATIVA',
        es_obligatoria=True,
        created_by=None
    )
    db.add(seccion_9_1)
    secciones_v2['9.1'] = seccion_9_1
    
    seccion_9_2 = SeccionFormulario(
        id=uuid.uuid4(),
        formulario_id=formulario_v2.id,
        numero_seccion='9.2',
        titulo='MONTO DE OPERACIONES REALIZADAS',
        descripcion='Valores monetarios de notas de crédito y débito',
        orden=9,
        tipo_seccion='INFORMATIVA',
        es_obligatoria=True,
        created_by=None
    )
    db.add(seccion_9_2)
    secciones_v2['9.2'] = seccion_9_2
    
    await db.flush()
    print(f"✅ {len(secciones_v2)} secciones v2.0 creadas")
    
    # Duplicar casillas de v1.0 a v2.0 (excepto sección 9)
    casillas_v2 = []
    for casilla_v1 in todas_casillas_v1:
        if casilla_v1.seccion == '9':
            continue  # Saltar sección 9, la recreamos separada
        
        # Buscar sección correspondiente en v2.0
        seccion_v2 = secciones_v2.get(casilla_v1.seccion)
        if not seccion_v2:
            continue
        
        casilla_v2 = CasillaSat(
            id=uuid.uuid4(),
            seccion_id=seccion_v2.id,
            formulario_id=formulario_v2.id,
            codigo=casilla_v1.codigo,
            codigo_visual=casilla_v1.codigo_visual,
            nombre=casilla_v1.nombre,
            descripcion=casilla_v1.descripcion,
            seccion=casilla_v1.seccion,
            orden_seccion=casilla_v1.orden_seccion,
            tipo_casilla=casilla_v1.tipo_casilla,
            naturaleza=casilla_v1.naturaleza,
            formula_calculo=casilla_v1.formula_calculo,
            porcentaje_aplicable=casilla_v1.porcentaje_aplicable,
            campo_origen_factura=casilla_v1.campo_origen_factura,
            es_editable=casilla_v1.es_editable,
            requiere_justificacion=casilla_v1.requiere_justificacion,
            es_visible_usuario=casilla_v1.es_visible_usuario,
            created_by=None
        )
        db.add(casilla_v2)
        casillas_v2.append(casilla_v2)
    
    # Crear casillas para sección 9.1 (conteos)
    casillas_9_1_v2 = [
        {'codigo': '9.1.1', 'nombre': 'Facturas (incluidas anuladas) - Emitidas', 'tipo': 'CONTEO'},
        {'codigo': '9.1.2', 'nombre': 'Facturas (incluidas anuladas) - Recibidas', 'tipo': 'CONTEO'},
        {'codigo': '9.1.3', 'nombre': 'Factura y Declaración Unica Centroamericana FYDUCA - Emitidas', 'tipo': 'CONTEO'},
        {'codigo': '9.1.4', 'nombre': 'Factura y Declaración Unica Centroamericana FYDUCA - Recibidas', 'tipo': 'CONTEO'},
        {'codigo': '9.1.5', 'nombre': 'Constancias de exención - Emitidas', 'tipo': 'CONTEO'},
        {'codigo': '9.1.6', 'nombre': 'Constancias de exención - Recibidas', 'tipo': 'CONTEO'},
        {'codigo': '9.1.7', 'nombre': 'Constancias de adquisición de insumos de producción local - Emitidas', 'tipo': 'CONTEO'},
        {'codigo': '9.1.8', 'nombre': 'Constancias de adquisición de insumos de producción local - Recibidas', 'tipo': 'CONTEO'},
        {'codigo': '9.1.9', 'nombre': 'Constancias de retención de IVA - Emitidas', 'tipo': 'CONTEO'},
        {'codigo': '9.1.10', 'nombre': 'Constancias de retención de IVA - Recibidas', 'tipo': 'CONTEO'},
        {'codigo': '9.1.11', 'nombre': 'Facturas especiales - Emitidas', 'tipo': 'CONTEO'},
        {'codigo': '9.1.12', 'nombre': 'Facturas especiales - Recibidas', 'tipo': 'CONTEO'},
        {'codigo': '9.1.13', 'nombre': 'Notas de crédito - Emitidas', 'tipo': 'CONTEO'},
        {'codigo': '9.1.14', 'nombre': 'Notas de crédito - Recibidas', 'tipo': 'CONTEO'},
        {'codigo': '9.1.15', 'nombre': 'Notas de débito - Emitidas', 'tipo': 'CONTEO'},
        {'codigo': '9.1.16', 'nombre': 'Notas de débito - Recibidas', 'tipo': 'CONTEO'},
    ]
    
    for i, cas_data in enumerate(casillas_9_1_v2, 1):
        casilla = CasillaSat(
            id=uuid.uuid4(),
            seccion_id=seccion_9_1.id,
            formulario_id=formulario_v2.id,
            codigo=cas_data['codigo'],
            codigo_visual=cas_data['codigo'],
            nombre=cas_data['nombre'],
            seccion='9.1',
            orden_seccion=i,
            tipo_casilla=cas_data['tipo'],
            es_visible_usuario=True,
            created_by=None
        )
        db.add(casilla)
        casillas_v2.append(casilla)
    
    # Crear casillas para sección 9.2 (montos)
    casillas_9_2_v2 = [
        {'codigo': '9.2.1', 'nombre': 'Valor de las notas de crédito del período - Emitidos', 'tipo': 'REFERENCIA', 'es_editable': True},
        {'codigo': '9.2.2', 'nombre': 'Valor de las notas de crédito del período - Recibidos', 'tipo': 'REFERENCIA', 'es_editable': True},
        {'codigo': '9.2.3', 'nombre': 'Valor de las notas de débito del período - Emitidos', 'tipo': 'REFERENCIA', 'es_editable': True},
        {'codigo': '9.2.4', 'nombre': 'Valor de las notas de débito del período - Recibidos', 'tipo': 'REFERENCIA', 'es_editable': True},
    ]
    
    for i, cas_data in enumerate(casillas_9_2_v2, 1):
        casilla = CasillaSat(
            id=uuid.uuid4(),
            seccion_id=seccion_9_2.id,
            formulario_id=formulario_v2.id,
            codigo=cas_data['codigo'],
            codigo_visual=cas_data['codigo'],
            nombre=cas_data['nombre'],
            seccion='9.2',
            orden_seccion=i,
            tipo_casilla=cas_data['tipo'],
            es_editable=cas_data.get('es_editable', False),
            es_visible_usuario=True,
            created_by=None
        )
        db.add(casilla)
        casillas_v2.append(casilla)
    
    await db.flush()
    print(f"✅ {len(casillas_v2)} casillas v2.0 creadas")
    
    # =========================================================================
    # REGLAS DE FILTRADO (solo para v2.0 - la versión activa)
    # =========================================================================
    print("\n📋 Creando reglas de filtrado para v2.0...")
    
    def get_casilla_v2(codigo):
        return next((c for c in casillas_v2 if c.codigo == codigo), None)
    
    reglas_data = [
        # Sección 3: Débito Fiscal Local
        {'casilla': '3.1', 'nombre': 'Ventas Exentas', 'criterios': {'tipo_operacion': 'Venta', 'es_exento': True, 'es_exportacion': False}, 'campo': 'total_exento_gtq'},
        {'casilla': '3.6', 'nombre': 'Ventas de Bienes Gravados', 'criterios': {'tipo_operacion': 'Venta', 'es_exento': False, 'es_exportacion': False, 'bien_o_servicio': 'B'}, 'campo': 'total_gravado_bienes_gtq'},
        {'casilla': '3.7', 'nombre': 'Ventas de Servicios Gravados', 'criterios': {'tipo_operacion': 'Venta', 'es_exento': False, 'es_exportacion': False, 'bien_o_servicio': 'S'}, 'campo': 'total_gravado_servicios_gtq'},
        
        # Sección 4: Exportaciones
        {'casilla': '4.1', 'nombre': 'Exportaciones a Centroamérica (excepto Honduras)', 'criterios': {'tipo_operacion': 'Venta', 'es_exportacion': True, 'region': 'CENTROAMERICA', 'pais_destino': {'$ne': 'HND'}}, 'campo': 'total_gtq'},
        {'casilla': '4.2', 'nombre': 'Exportaciones al resto del mundo', 'criterios': {'tipo_operacion': 'Venta', 'es_exportacion': True, 'region': 'FUERA_CENTROAMERICA'}, 'campo': 'total_gtq'},
        {'casilla': '4.3', 'nombre': 'Transferencias FYDUCA', 'criterios': {'tipo_operacion': 'Venta', 'tipo_documento': 'FYDUCA'}, 'campo': 'total_gtq'},
        
        # Sección 5: Crédito Fiscal Local
        {'casilla': '5.6', 'nombre': 'Compras de Combustibles', 'criterios': {'tipo_operacion': 'Compra', 'clasificacion_gasto_sat': 'COMBUSTIBLE'}, 'campo': 'total_gravado_gtq'},
        {'casilla': '5.7', 'nombre': 'Otras Compras', 'criterios': {'tipo_operacion': 'Compra', 'clasificacion_gasto_sat': 'NORMAL', 'bien_o_servicio': 'B'}, 'campo': 'total_gravado_bienes_gtq'},
        {'casilla': '5.8', 'nombre': 'Servicios Adquiridos', 'criterios': {'tipo_operacion': 'Compra', 'clasificacion_gasto_sat': 'NORMAL', 'bien_o_servicio': 'S'}, 'campo': 'total_gravado_servicios_gtq'},
        {'casilla': '5.12', 'nombre': 'Compras de Activos Fijos', 'criterios': {'tipo_operacion': 'Compra', 'clasificacion_gasto_sat': 'ACTIVO_FIJO'}, 'campo': 'total_gravado_gtq'},
    ]
    
    reglas_creadas = 0
    for regla_data in reglas_data:
        casilla = get_casilla_v2(regla_data['casilla'])
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
    print("\n📋 Creando exclusiones...")
    
    casilla_4_1 = get_casilla_v2('4.1')
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
    print("\n📋 Asociando con regímenes fiscales...")
    
    regimenes_sat_2237 = ['RG_UTILIDADES', 'RG_FEL']
    
    for codigo_regimen in regimenes_sat_2237:
        # Buscar régimen
        result = await db.execute(
            RegimenFiscal.__table__.select().where(
                RegimenFiscal.codigo == codigo_regimen
            )
        )
        regimen = result.scalar_one_or_none()
        
        if regimen:
            # Verificar si ya existe la asociación
            result = await db.execute(
                RegimenFormularioSat.__table__.select().where(
                    RegimenFormularioSat.regimen_id == regimen.id,
                    RegimenFormularioSat.formulario_id == formulario_v2.id
                )
            )
            existente = result.scalar_one_or_none()
            
            if not existente:
                asociacion = RegimenFormularioSat(
                    id=uuid.uuid4(),
                    regimen_id=regimen.id,
                    formulario_id=formulario_v2.id,
                    es_obligatorio=True,
                    created_by=None
                )
                db.add(asociacion)
                print(f"✅ SAT-2237 v2.0 asociado a régimen {codigo_regimen}")
        else:
            print(f"⚠️  Régimen no encontrado: {codigo_regimen}")
    
    # =========================================================================
    # COMMIT FINAL
    # =========================================================================
    await db.commit()
    
    print("\n" + "="*70)
    print("✅ SEED SAT-2237 COMPLETO FINALIZADO")
    print("="*70)
    print("\n📊 RESUMEN:")
    print(f"  Versión 1.0 (2025): {formulario_v1.id}")
    print("    - Vigencia: 2025-01-01 a 2025-12-31")
    print("    - Estado: Inactiva")
    print(f"    - Secciones: {len(secciones_v1)}")
    print(f"    - Casillas: {len(todas_casillas_v1)}")
    print(f"\n  Versión 2.0 (2026): {formulario_v2.id}")
    print("    - Vigencia: 2026-01-01 a presente")
    print("    - Estado: Activa")
    print("    - Basada en: v1.0")
    print(f"    - Secciones: {len(secciones_v2)}")
    print(f"    - Casillas: {len(casillas_v2)}")
    print("    - Mejoras: Secciones 9.1 y 9.2 separadas")
    print(f"\n  Reglas de filtrado: {reglas_creadas}")
    print("  Exclusiones: 1 (FYDUCA)")
    print("="*70)
    
    return formulario_v1, formulario_v2


async def main():
    """Función principal asíncrona"""
    from app.db.session import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            await seed_sat_2237_completo(db)
            print("\n🎉 Seed ejecutado correctamente")
        except Exception as e:
            await db.rollback()
            print(f"❌ Error ejecutando seed: {e}")
            traceback.print_exc()
            raise


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())