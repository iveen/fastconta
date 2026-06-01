# app/services/banguat_ws.py
import logging
import xml.etree.ElementTree as ET
from datetime import date
from decimal import Decimal

import requests
from app.models.global_models import CatalogoMoneda
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

BANGUAT_WS_URL = "https://www.banguat.gob.gt/variables/ws/TipoCambio.asmx"
BANGUAT_NS = "http://www.banguat.gob.gt/variables/ws/"
_cache: dict[tuple[str, str], Decimal] = {}

async def obtener_tipo_cambio(fecha: date, moneda_iso: str, db: AsyncSession) -> Decimal | None:
    """
    Consulta tipo de cambio venta al WS de Banguat.
    Busca el codigo_banguat dinámicamente desde la BD.
    """
    # GTQ siempre es 1.00000
    if moneda_iso.upper() == "GTQ":
        return Decimal("1.00000")
    
    # 🔹 1. Buscar código Banguat en BD
    result = await db.execute(
        select(CatalogoMoneda.codigo_banguat).where(
            CatalogoMoneda.codigo_iso == moneda_iso.upper(),
            CatalogoMoneda.activo is True
        )
    )
    codigo_banguat = result.scalar_one_or_none()
    
    if not codigo_banguat:
        logger.warning(f"⚠️ Moneda {moneda_iso} no encontrada en catálogo_monedas")
        return None

    fecha_str = fecha.strftime("%d/%m/%Y")
    cache_key = (fecha_str, codigo_banguat)
    
    if cache_key in _cache:
        return _cache[cache_key]

    # 🔹 2. SOAP Request
    soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
                 xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>
    <TipoCambioRangoMoneda xmlns="{BANGUAT_NS}">
      <fechainit>{fecha_str}</fechainit>
      <fechafin>{fecha_str}</fechafin>
      <moneda>{codigo_banguat}</moneda>
    </TipoCambioRangoMoneda>
  </soap12:Body>
</soap12:Envelope>"""
    
    headers = {
        "Content-Type": "application/soap+xml; charset=utf-8",
        "SOAPAction": f"{BANGUAT_NS}TipoCambioRangoMoneda"
    }
    
    try:
        response = requests.post(
            BANGUAT_WS_URL,
            data=soap_envelope.encode("utf-8"),
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        ns = {"soap": "http://www.w3.org/2003/05/soap-envelope", "banguat": BANGUAT_NS}
        
        venta_elem = root.find(".//banguat:venta", ns)
        if venta_elem is not None and venta_elem.text:
            tipo_cambio = Decimal(venta_elem.text.strip()).quantize(Decimal("0.00001"))
            _cache[cache_key] = tipo_cambio
            return tipo_cambio
            
        return None
        
    except Exception as e:
        logger.error(f"❌ Error consultando Banguat: {e}")
        return None