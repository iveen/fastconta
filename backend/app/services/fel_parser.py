from datetime import datetime
from lxml import etree
from typing import Optional, Dict

def parse_fel_xml(xml_content: str) -> Optional[Dict]:
    try:
        root = etree.fromstring(xml_content.encode('utf-8'))
    except Exception:
        return None

    # Buscar el namespace del DTE
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

    try:
        # Número de autorización (atributos Numero y Serie)
        aut_el = first(root.xpath('//dte:NumeroAutorizacion', namespaces=ns))
        if aut_el is None:
            return None
        numero_autorizacion = aut_el.get('Numero', '')
        serie = aut_el.get('Serie', '')

        # Fecha de emisión
        fecha_str = ''
        dg_el = first(root.xpath('//dte:DatosGenerales', namespaces=ns))
        if dg_el is not None:
            fecha_str = dg_el.get('FechaHoraEmision', '')
        fecha_emision = None
        if fecha_str:
            try:
                fecha_emision = datetime.fromisoformat(fecha_str)
            except ValueError:
                pass

        # Emisor (atributos)
        emisor_el = first(root.xpath('//dte:Emisor', namespaces=ns))
        emisor_nit = emisor_el.get('NITEmisor', '') if emisor_el is not None else ''
        emisor_nombre = emisor_el.get('NombreComercial', '') or emisor_el.get('NombreEmisor', '') if emisor_el is not None else ''

        # Receptor
        receptor_el = first(root.xpath('//dte:Receptor', namespaces=ns))
        receptor_nit = ''
        receptor_nombre = ''
        if receptor_el is not None:
            receptor_nit = receptor_el.get('NITReceptor', '') or receptor_el.get('IDReceptor', '')
            receptor_nombre = receptor_el.get('NombreReceptor', '')

        # Totales
        total_gravado = 0.0
        total_iva = 0.0
        total_exento = 0.0
        gran_total = 0.0

        gran_total_el = first(root.xpath('//dte:GranTotal', namespaces=ns))
        if gran_total_el is not None:
            gran_total = float(gran_total_el.text.strip() or '0')

        # Impuestos totales
        for imp_el in root.xpath('//dte:Totales/dte:TotalImpuestos/dte:TotalImpuesto', namespaces=ns):
            nombre_imp = imp_el.get('NombreCorto', '')
            monto_imp = float(imp_el.get('TotalMontoImpuesto', '0') or '0')
            if nombre_imp == 'IVA':
                total_iva = monto_imp

        # Items (para total gravado)
        for item_el in root.xpath('//dte:Items/dte:Item', namespaces=ns):
            for imp_el in item_el.xpath('.//dte:Impuesto', namespaces=ns):
                nombre_imp = imp_el.get('NombreCorto', '') or (first(imp_el.xpath('.//dte:NombreCorto', namespaces=ns)).text.strip() if first(imp_el.xpath('.//dte:NombreCorto', namespaces=ns)) is not None else '')
                if nombre_imp == 'IVA':
                    gravable_el = imp_el.get('MontoGravable') or (first(imp_el.xpath('.//dte:MontoGravable', namespaces=ns)).text.strip() if first(imp_el.xpath('.//dte:MontoGravable', namespaces=ns)) is not None else '0')
                    total_gravado += float(gravable_el)

        # Tipo documento y moneda
        tipo_documento = dg_el.get('Tipo', 'FACT') if dg_el is not None else 'FACT'
        moneda = dg_el.get('CodigoMoneda', 'GTQ') if dg_el is not None else 'GTQ'
        
        # Cargar Items a Factura Detalle
        items = []
        for item_el in root.xpath('//dte:Items/dte:Item', namespaces=ns):
            # Cantidad
            cantidad_el = item_el.find('dte:Cantidad', ns)
            cantidad = float(cantidad_el.text.strip()) if cantidad_el is not None and cantidad_el.text else 0.0

            # Descripción
            desc_el = item_el.find('dte:Descripcion', ns)
            descripcion = desc_el.text.strip() if desc_el is not None and desc_el.text else ''

            # Precio Unitario
            precio_unit_el = item_el.find('dte:PrecioUnitario', ns)
            precio_unitario = float(precio_unit_el.text.strip()) if precio_unit_el is not None and precio_unit_el.text else 0.0

            # Total línea
            total_linea_el = item_el.find('dte:Total', ns)
            total_linea = float(total_linea_el.text.strip()) if total_linea_el is not None and total_linea_el.text else 0.0

            # IVA por línea
            iva_linea = 0.0
            for imp_el in item_el.xpath('.//dte:Impuesto', namespaces=ns):
                nombre_imp_el = imp_el.find('dte:NombreCorto', ns)
                nombre_imp = nombre_imp_el.text.strip() if nombre_imp_el is not None and nombre_imp_el.text else ''
                if nombre_imp == 'IVA':
                    monto_imp_el = imp_el.find('dte:MontoImpuesto', ns)
                    iva_linea = float(monto_imp_el.text.strip()) if monto_imp_el is not None and monto_imp_el.text else 0.0

            items.append({
                'cantidad': cantidad,
                'descripcion': descripcion,
                'precio_unitario': precio_unitario,
                'total_linea': total_linea,
                'iva_linea': iva_linea,
            })

        # Detectar si es factura de exportación (complemento cex:Exportacion)
        es_exportacion = False
        cex_ns = None
        for val in root.nsmap.values():
            if val and 'ComplementoExportaciones' in val:
                cex_ns = val
                break
        if cex_ns:
            export_el = root.xpath('//dte:Complementos/dte:Complemento/cex:Exportacion', namespaces={'dte': dte_ns, 'cex': cex_ns})
            es_exportacion = bool(export_el)

        return {
            'numero_autorizacion': numero_autorizacion,
            'serie': serie,
            'numero': numero_autorizacion,  # El número de factura es el mismo número de autorización
            'fecha_emision': fecha_emision,
            'emisor_nit': emisor_nit,
            'emisor_nombre': emisor_nombre,
            'receptor_nit': receptor_nit,
            'receptor_nombre': receptor_nombre,
            'total_gravado': total_gravado,
            'total_iva': total_iva,
            'total_exento': total_exento,
            'total': gran_total,
            'tipo_documento': tipo_documento,
            'moneda': moneda,
            'autorizacion_uuid': aut_el.text.strip() if aut_el.text else '',
            'items': items,
            'es_exportacion': es_exportacion,
        }
    except Exception:
        return None