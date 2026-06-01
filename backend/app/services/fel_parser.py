import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict

from app.services.banguat_ws import obtener_tipo_cambio
from lxml import etree
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

async def parse_fel_xml(xml_content: str, db: AsyncSession = None) -> Dict | None:
    try:
        # Parsear XML
        root = etree.fromstring(xml_content.encode('utf-8'))
    except Exception as e:
        logger.error(f"Error al parsear XML (Sintaxis): {e}")
        return None

    # Detectar Namespace
    dte_ns = None
    for val in root.nsmap.values():
        if val and 'dte/fel' in val:
            dte_ns = val
            break
    if not dte_ns:
        dte_ns = 'http://www.sat.gob.gt/dte/fel/0.2.0'
    
    ns = {'dte': dte_ns}

    def first(el_list):
        return el_list[0] if el_list else None

    def get_text(element, default=''):
        """Helper seguro para obtener texto de un elemento"""
        if element is not None and element.text:
            return element.text.strip()
        return default

    try:
        # 1. Número de autorización
        aut_el = first(root.xpath('//dte:NumeroAutorizacion', namespaces=ns))
        if aut_el is None:
            logger.warning("No se encontró NumeroAutorizacion")
            return None
            
        numero_autorizacion = aut_el.get('Numero', '')
        serie = aut_el.get('Serie', '')

        # 2. Datos Generales (Fecha, Moneda)
        dg_el = first(root.xpath('//dte:DatosGenerales', namespaces=ns))
        fecha_emision = None
        moneda = 'GTQ'
        
        if dg_el is not None:
            moneda = dg_el.get('CodigoMoneda', 'GTQ')
            fecha_str = dg_el.get('FechaHoraEmision', '')
            if fecha_str:
                try:
                    fecha_emision = datetime.fromisoformat(fecha_str)
                except ValueError:
                    pass # Mantener None si falla
        
        # 🔹 NUEVO: Determinar si es exportación
        es_exportacion = False
        # 1. Por atributo Exp="SI" en DatosGenerales
        if dg_el is not None and dg_el.get('Exp', '').upper() == 'SI':
            es_exportacion = True
        # 2. Por complemento cex:Exportacion (más robusto)
        for val in root.nsmap.values():
            if val and 'ComplementoExportaciones' in val:
                cex_ns = val
                if root.xpath('//cex:Exportacion', namespaces={'cex': cex_ns}):
                    es_exportacion = True
                break
        
        # 🔹 NUEVO: Obtener tipo de cambio desde Banguat
        tipo_cambio = None
        if fecha_emision and moneda:
            # Extraer solo la fecha (sin hora) para consultar Banguat
            fecha_consulta = fecha_emision.date() if hasattr(fecha_emision, 'date') else fecha_emision
            tipo_cambio = await obtener_tipo_cambio(fecha_emision.date(), moneda, db) or Decimal("1.00000")
            logger.debug(f"🔍 Tipo de cambio para {moneda} ({fecha_consulta}): {tipo_cambio}")

        # 3. Emisor
        emisor_el = first(root.xpath('//dte:Emisor', namespaces=ns))
        emisor_nit = emisor_el.get('NITEmisor', '').replace('-', '') if emisor_el is not None else ''
        emisor_nombre = ''
        if emisor_el is not None:
            emisor_nombre = emisor_el.get('NombreComercial', '') or emisor_el.get('NombreEmisor', '')

        # 4. Receptor
        receptor_el = first(root.xpath('//dte:Receptor', namespaces=ns))
        receptor_nit = ''
        receptor_nombre = ''
        if receptor_el is not None:
            receptor_nit = (receptor_el.get('NITReceptor', '') or receptor_el.get('IDReceptor', '')).replace('-', '')
            receptor_nombre = receptor_el.get('NombreReceptor', '')

        # 5. Totales
        gran_total_el = first(root.xpath('//dte:GranTotal', namespaces=ns))
        gran_total = float(get_text(gran_total_el, '0'))

        total_iva = 0.0
        total_gravado = 0.0

        # Buscar IVA en totales
        for imp_el in root.xpath('//dte:Totales/dte:TotalImpuestos/dte:TotalImpuesto', namespaces=ns):
            if imp_el.get('NombreCorto', '') == 'IVA' or get_text(imp_el.find('dte:NombreCorto', ns)) == 'IVA':
                total_iva = float(imp_el.get('TotalMontoImpuesto', '0'))

        # 6. Items (Líneas de detalle)
        items = []
        for item_el in root.xpath('//dte:Items/dte:Item', namespaces=ns):
            cantidad = float(get_text(item_el.find('dte:Cantidad', ns), '0'))
            descripcion = get_text(item_el.find('dte:Descripcion', ns))
            precio_unitario = float(get_text(item_el.find('dte:PrecioUnitario', ns), '0'))
            total_linea = float(get_text(item_el.find('dte:Total', ns), '0'))
            
            iva_linea = 0.0
            for imp_el in item_el.xpath('.//dte:Impuesto', namespaces=ns):
                nombre_imp = imp_el.get('NombreCorto', '') or get_text(imp_el.find('dte:NombreCorto', ns))
                if nombre_imp == 'IVA':
                    # Buscar MontoImpuesto (puede ser atributo o elemento)
                    monto_imp = imp_el.get('MontoImpuesto')
                    if monto_imp is None:
                        el_monto = imp_el.find('dte:MontoImpuesto', ns)
                        monto_imp = get_text(el_monto, '0')
                    iva_linea += float(monto_imp)
                
                # Calcular gravado si es IVA
                if nombre_imp == 'IVA':
                    gravable = imp_el.get('MontoGravable')
                    if gravable is None:
                        el_grav = imp_el.find('dte:MontoGravable', ns)
                        gravable = get_text(el_grav, '0')
                    total_gravado += float(gravable)

            items.append({
                'cantidad': cantidad,
                'descripcion': descripcion,
                'precio_unitario': precio_unitario,
                'total_linea': total_linea,
                'iva_linea': iva_linea,
            })

        # 7. Exportación
        es_exportacion = False
        for val in root.nsmap.values():
            if val and 'ComplementoExportaciones' in val:
                cex_ns = val
                if root.xpath('//cex:Exportacion', namespaces={'cex': cex_ns}):
                    es_exportacion = True
                break

        # 8. Tipo de Cambio (Lógica solicitada)
        # Si es GTQ, es 1.00000. Si es otra moneda, intentar buscar en MonedaRef o atributo.
        tipo_cambio = 1.00000 if moneda == 'GTQ' else None
        
        if moneda != 'GTQ':
            # Intentar buscar en Complemento o atributo de DatosGenerales
            moneda_ref_el = first(root.xpath('//dte:MonedaRef', namespaces=ns))
            if moneda_ref_el is not None:
                tc_val = moneda_ref_el.get('TipoCambio')
                if tc_val:
                    try:
                        tipo_cambio = float(tc_val)
                    except ValueError:
                        pass
            
            if tipo_cambio is None and dg_el is not None:
                tc_attr = dg_el.get('TipoCambio')
                if tc_attr:
                    try:
                        tipo_cambio = float(tc_attr)
                    except ValueError:
                        pass
            
            # Fallback seguro si no se encuentra
            if tipo_cambio is None:
                tipo_cambio = 1.0

        return {
            'numero_autorizacion': numero_autorizacion,
            'serie': serie,
            'numero': numero_autorizacion, # El número suele ser igual a la autorización o se extrae de otro lado
            'fecha_emision': fecha_emision,
            'emisor_nit': emisor_nit,
            'emisor_nombre': emisor_nombre,
            'receptor_nit': receptor_nit,
            'receptor_nombre': receptor_nombre,
            'total_gravado': total_gravado,
            'total_iva': total_iva,
            'total_exento': 0.0, # Se puede calcular: total - gravado - iva
            'total': gran_total,
            'tipo_documento': dg_el.get('Tipo', 'FACT') if dg_el is not None else 'FACT',
            'moneda': moneda,
            'autorizacion_uuid': aut_el.text.strip() if aut_el.text else '',
            'items': items,
            'es_exportacion': es_exportacion,
            'tipo_cambio': tipo_cambio,
        }

    except Exception as e:
        # 🔴 AQUÍ ESTÁ LA CLAVE: Loguear el error real para debug
        logger.error(f"Error crítico parseando XML: {e}", exc_info=True)
        return None