"""
Parser robusto para facturas FEL de Guatemala.
Usa local-name() para ignorar namespaces y funcionar con cualquier certificador.
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict

from lxml import etree
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.facturas.tipo_cambio_service import obtener_tipo_cambio

logger = logging.getLogger(__name__)

async def parse_fel_xml(xml_content: str, db: AsyncSession = None) -> Dict | None:
    """
    Parsea un XML FEL de Guatemala de forma robusta.
    Usa local-name() para ignorar namespaces y funcionar con cualquier certificador.
    """
    try:
        root = etree.fromstring(xml_content.encode("utf-8"))
    except Exception as e:
        logger.error(f"Error al parsear XML (Sintaxis): {e}")
        return None

    # ============================================================
    # HELPERS ROBUSTOS: Buscan por nombre local, ignorando namespaces
    # ============================================================
    def first_local(name: str):
        """Busca el primer elemento con el nombre local dado, ignorando namespaces."""
        elements = root.xpath(f"//*[local-name()='{name}']")
        return elements[0] if elements else None

    def get_text(element, default=""):
        """Helper seguro para obtener texto de un elemento."""
        if element is not None and element.text:
            return element.text.strip()
        return default

    try:
        # 1. Número de autorización
        aut_el = first_local("NumeroAutorizacion")
        if aut_el is None:
            logger.warning("No se encontró NumeroAutorizacion en el XML")
            return None
        
        numero_autorizacion = aut_el.get("Numero", "")
        serie = aut_el.get("Serie", "")

        # 2. Datos Generales
        dg_el = first_local("DatosGenerales")
        numero_dte = dg_el.get("Numero", "") if dg_el is not None else ""
        fecha_emision = None
        moneda = "GTQ"
        es_exportacion = False
        
        if dg_el is not None:
            moneda = dg_el.get("CodigoMoneda", "GTQ")
            fecha_str = dg_el.get("FechaHoraEmision", "")
            if fecha_str:
                try:
                    fecha_emision = datetime.fromisoformat(fecha_str)
                except ValueError:
                    pass
            if dg_el.get("Exp", "").upper() == "SI":
                es_exportacion = True

        # Detectar exportación por complemento (robusto a namespaces)
        if not es_exportacion:
            if root.xpath("//*[local-name()='Exportacion']"):
                es_exportacion = True

        # Extraer país de destino de exportación
        pais_destino = None
        if es_exportacion:
            cex_el = first_local("Exportacion")
            if cex_el is not None:
                pais_el = cex_el.xpath(".//*[local-name()='PaisConsignatario']")
                if pais_el:
                    pais_destino = pais_el[0].text.strip() if pais_el[0].text else None

        # 3. Tipo de cambio (Banguat)
        tipo_cambio = Decimal("1.00000")
        if moneda != "GTQ" and fecha_emision and db:
            try:
                fecha_consulta = fecha_emision.date() if hasattr(fecha_emision, "date") else fecha_emision
                tc_banguat = await obtener_tipo_cambio(fecha_consulta, moneda, db)
                if tc_banguat:
                    tipo_cambio = tc_banguat
                    logger.info(f"✅ Tipo de cambio {moneda} ({fecha_consulta}): {tipo_cambio}")
                else:
                    logger.warning(f"️ No se pudo obtener tipo de cambio para {moneda} ({fecha_consulta}), usando 1.00000")
            except Exception as e:
                logger.error(f"❌ Error consultando Banguat: {e}")
                if dg_el and dg_el.get("TipoCambio"):
                    try:
                        tipo_cambio = Decimal(dg_el.get("TipoCambio"))
                    except Exception:
                        pass

        # 4. Emisor
        emisor_el = first_local("Emisor")
        emisor_nit = emisor_el.get("NITEmisor", "").replace("-", "") if emisor_el is not None else ""
        emisor_nombre = ""
        if emisor_el is not None:
            emisor_nombre = emisor_el.get("NombreComercial", "") or emisor_el.get("NombreEmisor", "")

        # 5. Receptor
        receptor_el = first_local("Receptor")
        receptor_nit = ""
        receptor_nombre = ""
        if receptor_el is not None:
            receptor_nit = (receptor_el.get("NITReceptor", "") or receptor_el.get("IDReceptor", "")).replace("-", "")
            receptor_nombre = receptor_el.get("NombreReceptor", "")

        # 6. Totales
        gran_total_el = first_local("GranTotal")
        gran_total = float(get_text(gran_total_el, "0"))

        # 7. Items (Líneas de detalle)
        items = []
        total_gravado_bienes = 0.0
        total_iva_bienes = 0.0
        total_gravado_servicios = 0.0
        total_iva_servicios = 0.0
        
        # Buscar todos los Item dentro de Items (robusto a namespaces)
        item_els = root.xpath("//*[local-name()='Items']/*[local-name()='Item']")
        
        for item_el in item_els:
            cant_el = item_el.xpath(".//*[local-name()='Cantidad']")
            desc_el = item_el.xpath(".//*[local-name()='Descripcion']")
            precio_el = item_el.xpath(".//*[local-name()='PrecioUnitario']")
            total_el = item_el.xpath(".//*[local-name()='Total']")
            
            cantidad = float(get_text(cant_el[0] if cant_el else None, "0"))
            descripcion = get_text(desc_el[0] if desc_el else None)
            precio_unitario = float(get_text(precio_el[0] if precio_el else None, "0"))
            total_linea = float(get_text(total_el[0] if total_el else None, "0"))
            
            bien_o_servicio = item_el.get("BienOServicio", "B")
            
            iva_linea = 0.0
            gravable_linea = 0.0
            
            for imp_el in item_el.xpath(".//*[local-name()='Impuesto']"):
                nombre_corto_el = imp_el.xpath(".//*[local-name()='NombreCorto']")
                nombre_imp = get_text(nombre_corto_el[0] if nombre_corto_el else None)
                
                if nombre_imp == "IVA":
                    monto_imp_el = imp_el.xpath(".//*[local-name()='MontoImpuesto']")
                    iva_linea = float(get_text(monto_imp_el[0] if monto_imp_el else None, "0"))
                    
                    gravable_el = imp_el.xpath(".//*[local-name()='MontoGravable']")
                    gravable_linea = float(get_text(gravable_el[0] if gravable_el else None, "0"))
            
            if bien_o_servicio == "B":
                total_gravado_bienes += gravable_linea
                total_iva_bienes += iva_linea
            else:
                total_gravado_servicios += gravable_linea
                total_iva_servicios += iva_linea
                
            items.append({
                "cantidad": cantidad,
                "descripcion": descripcion,
                "precio_unitario": precio_unitario,
                "total_linea": total_linea,
                "iva_linea": iva_linea,
                "bien_o_servicio": bien_o_servicio,
            })

        # 8. Calcular totales en GTQ
        tc_float = float(tipo_cambio)
        total_gravado_bienes_gtq = total_gravado_bienes * tc_float
        total_iva_bienes_gtq = total_iva_bienes * tc_float
        total_gravado_servicios_gtq = total_gravado_servicios * tc_float
        total_iva_servicios_gtq = total_iva_servicios * tc_float

        return {
            "numero_autorizacion": numero_autorizacion,
            "serie": serie,
            "numero": numero_dte or numero_autorizacion[:8],
            "fecha_emision": fecha_emision,
            "emisor_nit": emisor_nit,
            "emisor_nombre": emisor_nombre,
            "receptor_nit": receptor_nit,
            "receptor_nombre": receptor_nombre,
            "total_gravado": total_gravado_bienes + total_gravado_servicios,
            "total_iva": total_iva_bienes + total_iva_servicios,
            "total_exento": 0.0,
            "total": gran_total,
            "tipo_documento": dg_el.get("Tipo", "FACT") if dg_el is not None else "FACT",
            "moneda": moneda,
            "autorizacion_uuid": aut_el.text.strip() if aut_el.text else "",
            "items": items,
            "es_exportacion": es_exportacion,
            "pais_destino_exportacion": pais_destino,
            "tipo_cambio": float(tipo_cambio),
            "total_gravado_bienes": total_gravado_bienes,
            "total_iva_bienes": total_iva_bienes,
            "total_gravado_servicios": total_gravado_servicios,
            "total_iva_servicios": total_iva_servicios,
            "total_gravado_bienes_gtq": total_gravado_bienes_gtq,
            "total_iva_bienes_gtq": total_iva_bienes_gtq,
            "total_gravado_servicios_gtq": total_gravado_servicios_gtq,
            "total_iva_servicios_gtq": total_iva_servicios_gtq,
        }
        
    except Exception as e:
        logger.error(f"Error crítico parseando XML: {e}", exc_info=True)
        return None
