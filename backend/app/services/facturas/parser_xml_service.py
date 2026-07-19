import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict

from app.services.facturas.tipo_cambio_service import obtener_tipo_cambio
from lxml import etree
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

async def parse_fel_xml(xml_content: str, db: AsyncSession = None) -> Dict | None:
    try:
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

        # 2. Datos Generales (Fecha, Moneda, Exportación)
        dg_el = first(root.xpath('//dte:DatosGenerales', namespaces=ns))
        numero_dte = dg_el.get('Numero', '') if dg_el is not None else ''
        fecha_emision = None
        moneda = 'GTQ'
        es_exportacion = False
        
        if dg_el is not None:
            moneda = dg_el.get('CodigoMoneda', 'GTQ')
            fecha_str = dg_el.get('FechaHoraEmision', '')
            if fecha_str:
                try:
                    fecha_emision = datetime.fromisoformat(fecha_str)
                except ValueError:
                    pass
            
            # Detectar exportación por atributo Exp="SI"
            if dg_el.get('Exp', '').upper() == 'SI':
                es_exportacion = True
        
        # 🔹 Detectar exportación por complemento cex:Exportacion
        if not es_exportacion:
            for val in root.nsmap.values():
                if val and 'ComplementoExportaciones' in val:
                    cex_ns = val
                    if root.xpath('//cex:Exportacion', namespaces={'cex': cex_ns}):
                        es_exportacion = True
                    break
        
        # 🔹 NUEVO: Extraer país de destino de exportación
        pais_destino = None
        if es_exportacion:
            for val in root.nsmap.values():
                if val and 'ComplementoExportaciones' in val:
                    cex_ns = val
                    export_el = first(root.xpath('//cex:Exportacion', namespaces={'cex': cex_ns}))
                    if export_el is not None:
                        pais_destino = export_el.findtext('cex:PaisConsignatario', namespaces={'cex': cex_ns})
                        if pais_destino:
                            pais_destino = pais_destino.strip()
                    break
        
        # 🔹 Obtener tipo de cambio desde Banguat (SOLO si no es GTQ)
        tipo_cambio = Decimal("1.00000")  # Default para GTQ
        
        if moneda != 'GTQ' and fecha_emision and db:
            try:
                fecha_consulta = fecha_emision.date() if hasattr(fecha_emision, 'date') else fecha_emision
                tc_banguat = await obtener_tipo_cambio(fecha_consulta, moneda, db)
                
                if tc_banguat:
                    tipo_cambio = tc_banguat
                    logger.info(f"✅ Tipo de cambio {moneda} ({fecha_consulta}): {tipo_cambio}")
                else:
                    logger.warning(f"⚠️ No se pudo obtener tipo de cambio para {moneda} ({fecha_consulta}), usando 1.00000")
            except Exception as e:
                logger.error(f"❌ Error consultando Banguat: {e}")
                # Si falla, buscar en el XML
                if dg_el and dg_el.get('TipoCambio'):
                    try:
                        tipo_cambio = Decimal(dg_el.get('TipoCambio'))
                    except Exception as e:
                        pass

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

        # 6. Items (Líneas de detalle) - CON CÁLCULOS SEPARADOS
        items = []
        total_gravado_bienes = 0.0
        total_iva_bienes = 0.0
        total_gravado_servicios = 0.0
        total_iva_servicios = 0.0

        for item_el in root.xpath('//dte:Items/dte:Item', namespaces=ns):
            cantidad = float(get_text(item_el.find('dte:Cantidad', ns), '0'))
            descripcion = get_text(item_el.find('dte:Descripcion', ns))
            precio_unitario = float(get_text(item_el.find('dte:PrecioUnitario', ns), '0'))
            total_linea = float(get_text(item_el.find('dte:Total', ns), '0'))
            
            # 🔹 Extraer BienOServicio
            bien_o_servicio = item_el.get('BienOServicio', 'B')  # Default 'B' si no viene
            
            iva_linea = 0.0
            gravable_linea = 0.0
            
            for imp_el in item_el.xpath('.//dte:Impuesto', namespaces=ns):
                nombre_imp = imp_el.get('NombreCorto', '') or get_text(imp_el.find('dte:NombreCorto', ns))
                if nombre_imp == 'IVA':
                    # Buscar MontoImpuesto
                    monto_imp = imp_el.get('MontoImpuesto')
                    if monto_imp is None:
                        el_monto = imp_el.find('dte:MontoImpuesto', ns)
                        monto_imp = get_text(el_monto, '0')
                    iva_linea = float(monto_imp)
                    
                    # Buscar MontoGravable
                    gravable = imp_el.get('MontoGravable')
                    if gravable is None:
                        el_grav = imp_el.find('dte:MontoGravable', ns)
                        gravable = get_text(el_grav, '0')
                    gravable_linea = float(gravable)

            # 🔹 Acumular según tipo (BIEN o SERVICIO)
            if bien_o_servicio == 'B':
                total_gravado_bienes += gravable_linea
                total_iva_bienes += iva_linea
            else:  # 'S' - Servicio
                total_gravado_servicios += gravable_linea
                total_iva_servicios += iva_linea

            items.append({
                'cantidad': cantidad,
                'descripcion': descripcion,
                'precio_unitario': precio_unitario,
                'total_linea': total_linea,
                'iva_linea': iva_linea,
                'bien_o_servicio': bien_o_servicio,
            })

        # 🔹 Calcular totales en GTQ separados
        tc_float = float(tipo_cambio)
        total_gravado_bienes_gtq = total_gravado_bienes * tc_float
        total_iva_bienes_gtq = total_iva_bienes * tc_float
        total_gravado_servicios_gtq = total_gravado_servicios * tc_float
        total_iva_servicios_gtq = total_iva_servicios * tc_float

        return {
            'numero_autorizacion': numero_autorizacion,
            'serie': serie,
            'numero': numero_dte or numero_autorizacion[:8],
            'fecha_emision': fecha_emision,
            'emisor_nit': emisor_nit,
            'emisor_nombre': emisor_nombre,
            'receptor_nit': receptor_nit,
            'receptor_nombre': receptor_nombre,
            'total_gravado': total_gravado_bienes + total_gravado_servicios,  # Total general
            'total_iva': total_iva_bienes + total_iva_servicios,  # Total general
            'total_exento': 0.0,
            'total': gran_total,
            'tipo_documento': dg_el.get('Tipo', 'FACT') if dg_el is not None else 'FACT',
            'moneda': moneda,
            'autorizacion_uuid': aut_el.text.strip() if aut_el.text else '',
            'items': items,
            'es_exportacion': es_exportacion,
            'pais_destino_exportacion': pais_destino,
            'tipo_cambio': float(tipo_cambio),
            
            # 🔹 NUEVOS: Totales separados por bienes/servicios (moneda original)
            'total_gravado_bienes': total_gravado_bienes,
            'total_iva_bienes': total_iva_bienes,
            'total_gravado_servicios': total_gravado_servicios,
            'total_iva_servicios': total_iva_servicios,
            
            # 🔹 NUEVOS: Totales separados por bienes/servicios (en GTQ)
            'total_gravado_bienes_gtq': total_gravado_bienes_gtq,
            'total_iva_bienes_gtq': total_iva_bienes_gtq,
            'total_gravado_servicios_gtq': total_gravado_servicios_gtq,
            'total_iva_servicios_gtq': total_iva_servicios_gtq,
        }

    except Exception as e:
        logger.error(f"Error crítico parseando XML: {e}", exc_info=True)
        return None