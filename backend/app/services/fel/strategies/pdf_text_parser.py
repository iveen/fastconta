"""
Parser de texto para FEL Guatemala.
Extrae datos de PDFs sin XML embebido usando regex.
Formato estándar SAT Guatemala (certificadores como FACTUS, INFILE, etc.)
"""
import logging
import re
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional

logger = logging.getLogger(__name__)


async def parse_fel_texto(texto: str) -> Optional[Dict]:
    """
    Parsea el texto extraído de un PDF FEL.
    Retorna dict con datos o None si no puede parsear.
    """
    if not texto or len(texto) < 100:
        logger.warning("Texto demasiado corto para parsear")
        return None

    try:
        # Normalizar saltos de línea para facilitar el parsing
        texto_normalizado = texto.replace('\r\n', '\n').replace('\r', '\n')
        
        # 1. Número de autorización (UUID) - PRIMERO porque es crítico
        # Formato: "32D9D9B1-8BB3-4316-8E4C-833304CA9D2C"
        uuid_pattern = r'([0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12})'
        uuid_match = re.search(uuid_pattern, texto_normalizado, re.IGNORECASE)
        if not uuid_match:
            logger.warning("No se encontró número de autorización (UUID)")
            return None
        
        numero_autorizacion = uuid_match.group(1).upper()
        logger.info(f"✅ UUID encontrado: {numero_autorizacion}")

        # 2. NIT Emisor
        nit_emisor_pattern = r'Nit\s+Emisor[:\s]+(\d{6,10})'
        nit_emisor_match = re.search(nit_emisor_pattern, texto_normalizado, re.IGNORECASE)
        emisor_nit = nit_emisor_match.group(1) if nit_emisor_match else ""
        logger.info(f"✅ NIT Emisor: {emisor_nit}")

        # 3. Nombre Emisor - CORREGIDO
        # Buscar la primera línea que termine antes de "NÚMERO DE AUTORIZACIÓN"
        emisor_nombre = ""
        lines = texto_normalizado.split('\n')
        for i, line in enumerate(lines):
            if 'Nit Emisor' in line:
                # Buscar en líneas anteriores (empezando desde la más cercana)
                for j in range(i-1, max(0, i-4), -1):
                    candidate = lines[j].strip()
                    # Excluir líneas que contengan "Factura" o "NÚMERO DE AUTORIZACIÓN"
                    if (candidate and 
                        'Factura' not in candidate and 
                        'NÚMERO DE AUTORIZACIÓN' not in candidate and
                        len(candidate) > 10):
                        # Limpiar el nombre - quitar todo después de "SOCIEDAD" o similar
                        emisor_nombre = candidate.split('NÚMERO DE AUTORIZACIÓN')[0].strip()
                        emisor_nombre = re.sub(r'\s+', ' ', emisor_nombre)  # Normalizar espacios
                        break
                break
        
        # Si no se encontró, buscar patrón alternativo
        if not emisor_nombre:
            nombre_pattern = r'^([A-ZÁÉÍÓÚÑ\s&,\.]+(?:SOCIEDAD\s+ANÓNIMA|S\.A\.)[A-ZÁÉÍÓÚÑ\s&,\.]*)'
            nombre_match = re.search(nombre_pattern, texto_normalizado, re.MULTILINE)
            if nombre_match:
                emisor_nombre = nombre_match.group(1).strip()
                emisor_nombre = emisor_nombre.split('NÚMERO DE AUTORIZACIÓN')[0].strip()

        logger.info(f"✅ Nombre Emisor: {emisor_nombre}")

        # 4. Serie
        serie_pattern = r'Serie[:\s]+([A-Z0-9]{1,20})'
        serie_match = re.search(serie_pattern, texto_normalizado, re.IGNORECASE)
        serie = serie_match.group(1) if serie_match else numero_autorizacion[:8]
        logger.info(f"✅ Serie: {serie}")

        # 5. Número de DTE
        num_dte_pattern = r'Número\s+de\s+DTE[:\s]+(\d+)'
        num_dte_match = re.search(num_dte_pattern, texto_normalizado, re.IGNORECASE)
        numero = num_dte_match.group(1) if num_dte_match else None
        logger.info(f"✅ Número DTE: {numero}")

        # 6. ID/NIT Receptor
        nit_receptor_pattern = r'(?:ID\s+extranjero\s+Receptor|NIT\s+Receptor)[:\s]+(\d{6,13})'
        nit_receptor_match = re.search(nit_receptor_pattern, texto_normalizado, re.IGNORECASE)
        receptor_nit = nit_receptor_match.group(1) if nit_receptor_match else ""
        logger.info(f"✅ NIT/ID Receptor: {receptor_nit}")

        # 7. Nombre Receptor - CORREGIDO
        # Buscar "Nombre Receptor:" y capturar hasta encontrar "Fecha"
        receptor_nombre = ""
        receptor_pattern = r'Nombre\s+Receptor[:\s]+([^\n]+?)(?=\s+Fecha\s+y\s+hora|\s+Dirección|\s*$)'
        receptor_match = re.search(receptor_pattern, texto_normalizado, re.IGNORECASE)
        if receptor_match:
            receptor_nombre = receptor_match.group(1).strip()
            # Limpiar cualquier texto adicional
            receptor_nombre = re.sub(r'\s+Fecha.*$', '', receptor_nombre, flags=re.IGNORECASE)
            receptor_nombre = receptor_nombre.strip()

        logger.info(f"✅ Nombre Receptor: {receptor_nombre}")

        # 8. Fecha y hora de emisión
        fecha_pattern = r'(\d{1,2}-\w{3}-\d{4}\s+\d{1,2}:\d{2}:\d{2})'
        fecha_match = re.search(fecha_pattern, texto_normalizado, re.IGNORECASE)
        fecha_emision = None
        if fecha_match:
            try:
                fecha_str = fecha_match.group(1)
                fecha_emision = datetime.strptime(fecha_str, "%d-%b-%Y %H:%M:%S")
                logger.info(f"✅ Fecha emisión: {fecha_emision}")
            except Exception as e:
                logger.warning(f"Error parseando fecha: {e}")

        # 9. Moneda
        moneda_pattern = r'Moneda[:\s]+(GTQ|USD|EUR)'
        moneda_match = re.search(moneda_pattern, texto_normalizado, re.IGNORECASE)
        moneda = moneda_match.group(1).upper() if moneda_match else "GTQ"
        logger.info(f"✅ Moneda: {moneda}")

        # 10. Total - CORREGIDO
        # Buscar línea de TOTALES y capturar el último número antes de "IVA"
        # Formato: "TOTALES: 0.00 0.00 6,975.81 IVA 0.000000"
        total_line_pattern = r'TOTALES:.*?([\d,]+\.\d{2})\s+IVA'
        total_match = re.search(total_line_pattern, texto_normalizado, re.IGNORECASE)
        total = Decimal("0")
        if total_match:
            try:
                total_str = total_match.group(1).replace(",", "")
                total = Decimal(total_str)
                logger.info(f"✅ Total: {total}")
            except Exception as e:
                logger.warning(f"Error parseando total: {e}")
                # Fallback: buscar cualquier número después de TOTALES
                fallback_pattern = r'TOTALES:[\s\d,.]+([\d,]+\.\d{2})'
                fallback_match = re.search(fallback_pattern, texto_normalizado)
                if fallback_match:
                    total_str = fallback_match.group(1).replace(",", "")
                    total = Decimal(total_str)

        # 11. IVA
        iva_pattern = r'IVA\s+([\d.]+)'
        iva_matches = re.findall(iva_pattern, texto_normalizado)
        total_iva = Decimal("0")
        if iva_matches:
            try:
                total_iva = Decimal(iva_matches[-1])
                logger.info(f"✅ IVA Total: {total_iva}")
            except: #noqa E722
                pass

        # 12. Calcular total gravado
        total_gravado = total - total_iva if total > 0 else Decimal("0")
        logger.info(f"✅ Total Gravado: {total_gravado}")

        # 13. Detectar exportación
        es_exportacion = bool(re.search(r'Exportacion|ID\s+extranjero|COMPLEMENTO\s+EXPORTACION', texto_normalizado, re.IGNORECASE))
        logger.info(f"✅ Es exportación: {es_exportacion}")

        # 14. País de destino (si es exportación)
        pais_destino = None
        if es_exportacion:
            pais_pattern = r'País\s+del\s+consignatario[:\s]+([^\n]+)'
            pais_match = re.search(pais_pattern, texto_normalizado, re.IGNORECASE)
            if pais_match:
                pais_destino = pais_match.group(1).strip()
                logger.info(f"✅ País destino: {pais_destino}")

        # 15. Tipo de documento
        tipo_documento = "FACT"
        if re.search(r'FACTURA\s+CAMBIARIA|FCAM', texto_normalizado, re.IGNORECASE):
            tipo_documento = "FCAM"
        elif re.search(r'NOTA\s+DE\s+CRÉDITO|NCRE', texto_normalizado, re.IGNORECASE):
            tipo_documento = "NCRE"
        elif re.search(r'NOTA\s+DE\s+DÉBITO|NDEB', texto_normalizado, re.IGNORECASE):
            tipo_documento = "NDEB"
        logger.info(f"✅ Tipo documento: {tipo_documento}")

        # 16. Items - CORREGIDO para manejar descripciones multilínea
        items = []

        # Primero, normalizar el texto: unir líneas que sean continuación de descripciones
        lineas = texto_normalizado.split('\n')
        lineas_procesadas = []
        i = 0

        while i < len(lineas):
            linea_actual = lineas[i].strip()
            
            # Si la línea actual parece un item (empieza con número + Servicio/Bien)
            if re.match(r'^\d+\s+(Servicio|Bien)', linea_actual, re.IGNORECASE):
                descripcion_completa = linea_actual
                j = i + 1
                
                # Buscar líneas de continuación (texto en mayúsculas sin número al inicio)
                while j < len(lineas):
                    linea_sig = lineas[j].strip()
                    
                    # Es continuación si:
                    # 1. No está vacía
                    # 2. No empieza con número
                    # 3. No es "TOTALES" ni otra palabra clave
                    # 4. Es texto corto (< 50 chars)
                    # 5. Está en mayúsculas o es una palabra sola
                    if (linea_sig and 
                        not re.match(r'^\d+', linea_sig) and 
                        not re.match(r'^(TOTALES|IVA|Impuestos)', linea_sig, re.IGNORECASE) and
                        len(linea_sig) < 50 and
                        (linea_sig.isupper() or len(linea_sig.split()) == 1)):
                        
                        descripcion_completa += " " + linea_sig
                        j += 1
                    else:
                        break
                
                lineas_procesadas.append(descripcion_completa)
                i = j
            else:
                lineas_procesadas.append(linea_actual)
                i += 1

        texto_unificado = '\n'.join(lineas_procesadas)

        # Ahora parsear items con el texto unificado
        # Patrón: número + tipo + cantidad + descripción + precios
        item_pattern = r'^\s*(\d+)\s+(Servicio|Bien)\s+(\d+(?:\.\d+)?)\s+([A-Z\s]+?)\s+([\d,]+\.\d{2})\s+[\d,.]+\s+[\d,.]+\s+([\d,]+\.\d{2})'

        for match in re.finditer(item_pattern, texto_unificado, re.MULTILINE | re.IGNORECASE):
            try:
                descripcion = match.group(4).strip()
                # Limpiar descripción (normalizar espacios múltiples)
                descripcion = re.sub(r'\s+', ' ', descripcion)
                
                precio_str = match.group(5).replace(",", "")
                total_str = match.group(6).replace(",", "")
                
                items.append({
                    "cantidad": float(match.group(3)),
                    "descripcion": descripcion,
                    "precio_unitario": float(precio_str),
                    "total_linea": float(total_str),
                    "iva_linea": 0.0,
                    "bien_o_servicio": "S" if match.group(2).lower() == "servicio" else "B"
                })
                
                logger.info(f"✅ Item parseado: {descripcion} - Total: {total_str}")
                
            except Exception as e:
                logger.warning(f"Error parseando item: {e}")

        logger.info(f"✅ Items encontrados: {len(items)}")

        # 17. Determinar totales por bienes/servicios
        if es_exportacion:
            total_gravado_servicios = float(total_gravado)
            total_iva_servicios = float(total_iva)
            total_gravado_bienes = 0.0
            total_iva_bienes = 0.0
        else:
            total_gravado_servicios = sum(
                item["total_linea"] for item in items if item["bien_o_servicio"] == "S"
            )
            total_iva_servicios = sum(
                item["iva_linea"] for item in items if item["bien_o_servicio"] == "S"
            )
            total_gravado_bienes = sum(
                item["total_linea"] for item in items if item["bien_o_servicio"] == "B"
            )
            total_iva_bienes = sum(
                item["iva_linea"] for item in items if item["bien_o_servicio"] == "B"
            )

        return {
            "numero_autorizacion": numero_autorizacion,
            "serie": serie,
            "numero": numero or numero_autorizacion[:8],
            "fecha_emision": fecha_emision,
            "emisor_nit": emisor_nit,
            "emisor_nombre": emisor_nombre,
            "receptor_nit": receptor_nit,
            "receptor_nombre": receptor_nombre,
            "total_gravado": float(total_gravado),
            "total_iva": float(total_iva),
            "total_exento": 0.0,
            "total": float(total),
            "tipo_documento": tipo_documento,
            "moneda": moneda,
            "items": items,
            "es_exportacion": es_exportacion,
            "pais_destino_exportacion": pais_destino,
            "tipo_cambio": 1.0,
            "total_gravado_bienes": total_gravado_bienes,
            "total_iva_bienes": total_iva_bienes,
            "total_gravado_servicios": total_gravado_servicios,
            "total_iva_servicios": total_iva_servicios,
            "total_gravado_bienes_gtq": 0.0,
            "total_iva_bienes_gtq": 0.0,
            "total_gravado_servicios_gtq": 0.0,
            "total_iva_servicios_gtq": 0.0,
        }

    except Exception as e:
        logger.error(f"Error crítico parseando texto FEL: {e}", exc_info=True)
        return None