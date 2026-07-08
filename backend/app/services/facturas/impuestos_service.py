# app/services/facturas_service.py

from decimal import Decimal

from app.models.global_models import CatalogoImpuestoEspecial
from app.models.tenant_models import FacturaElectronica, FacturaImpuestoEspecial
from sqlalchemy.orm import Session  # ✅ 1. AQUÍ VA EL IMPORT DE SESSION

# ✅ 2. AQUÍ VA EL MAPEO: Traduce las columnas del Excel/XML de la SAT a tus códigos de BD
MAPA_IMPUESTOS_ESPECIALES_SAT = {
    "Petróleo (monto de este impuesto)": "PETROLEO",
    "Turismo Hospedaje (monto de este impuesto)": "TURISMO_HOSPEDAJE",
    "Turismo Pasajes (monto de este impuesto)": "TURISMO_PASAJES",
    "Timbre de Prensa (monto de este impuesto)": "TIMBRE_PRENSA",
    "Bomberos (monto de este impuesto)": "BOMBEROS",
    "Tasa Municipal (monto de este impuesto)": "TASA_MUNICIPAL",
    "Bebidas Alcoholicas (monto de este impuesto)": "BEBIDAS_ALCOHOLICAS",
    "Tabaco (monto de este impuesto)": "TABACO",
    "Cemento (monto de este impuesto)": "CEMENTO",
    "Bebidas no Alcoholicas (monto de este impuesto)": "BEBIDAS_NO_ALCOHOLICAS",
    "Tarifa Portuaria (monto de este impuesto)": "TARIFA_PORTUARIA",
    "Vehiculos IPRIMA (monto de este impuesto)": "VEHICULOS_IPRIMA"
}


def validar_calculo_iva(factura_data: dict) -> dict:
    """
    Solo VALIDA que el cálculo del IVA sea correcto según la Ley (Art. 11 Ley 27-92).
    No guarda nada en la base de datos. Retorna los valores calculados.
    """
    gran_total = Decimal(str(factura_data.get("gran_total", 0) or 0))
    tasa_iva = Decimal("0.12")  # 12% general
    
    # 1. Extraer montos usando el mapa de la SAT
    total_impuestos_especiales = Decimal("0.00")
    impuestos_detectados = {}
    
    for columna_sat, codigo_bd in MAPA_IMPUESTOS_ESPECIALES_SAT.items():
        monto = Decimal(str(factura_data.get(columna_sat, 0) or 0))
        if monto > 0:
            total_impuestos_especiales += monto
            impuestos_detectados[codigo_bd] = monto
    
    # 2. Calcular la base imponible del IVA (Gran Total - Impuestos Especiales)
    base_imponible_iva = gran_total - total_impuestos_especiales
    
    # 3. Calcular el IVA esperado
    iva_calculado = (base_imponible_iva * tasa_iva).quantize(Decimal("0.01"))
    
    # 4. Validar contra el IVA declarado en la factura (tolerancia de 1 centavo)
    iva_factura = Decimal(str(factura_data.get("iva", 0) or 0))
    if abs(iva_calculado - iva_factura) > Decimal("0.01"):
        raise ValueError(
            f"El IVA de la factura ({iva_factura}) no coincide con el calculado ({iva_calculado}). "
            f"Total Impuestos Especiales detectados: {total_impuestos_especiales}. "
            f"Verifique que los montos de la columna W-AG del reporte SAT sean correctos."
        )
    
    return {
        "base_imponible_iva": base_imponible_iva,
        "iva_valido": iva_calculado,
        "impuestos_especiales_detectados": impuestos_detectados,
        "total_impuestos_especiales": total_impuestos_especiales
    }


def guardar_impuestos_especiales_factura(
    db: Session, 
    factura: FacturaElectronica, 
    impuestos_detectados: dict
) -> None:
    """
    Guarda los registros en la tabla puente 'facturas_impuestos_especiales'.
    """
    for codigo_bd, monto in impuestos_detectados.items():
        # Buscar el catálogo global (esquema public)
        catalogo = db.query(CatalogoImpuestoEspecial).filter_by(codigo=codigo_bd).first()
        
        if catalogo:
            # Crear el registro en la tabla del tenant
            impuesto_registro = FacturaImpuestoEspecial(
                factura_id=factura.id,
                catalogo_id=catalogo.id,
                monto=monto
            )
            db.add(impuesto_registro)
    
    db.commit()