"""
Configuración de Impuestos por Régimen Fiscal (Tabla Puente)
Define las tasas, acreditabilidad y límites específicos para cada combinación.
"""
from decimal import Decimal

# Usamos códigos de referencia que el script de seed resolverá a IDs
REGIMEN_IMPUESTO_CONFIG = [
    # --- PEQUEÑO CONTRIBUYENTE MANUAL ---
    {
        "regimen_codigo": "PC_MANUAL",
        "impuesto_codigo": "IVA_GENERAL",
        "tasa_porcentaje": Decimal("12.00"),
        "es_acreditable": False,
        "es_retencion_definitiva": True,
        "requiere_autorizacion_sat": False
    },
    {
        "regimen_codigo": "PC_MANUAL",
        "impuesto_codigo": "ISR",
        "tasa_porcentaje": Decimal("5.00"),
        "limite_superior": Decimal("300000.00"),
        "es_acreditable": False,
        "es_retencion_definitiva": True,
        "requiere_autorizacion_sat": False
    },
    # --- PEQUEÑO CONTRIBUYENTE FEL ---
    {
        "regimen_codigo": "PC_FEL",
        "impuesto_codigo": "IVA_GENERAL",
        "tasa_porcentaje": Decimal("12.00"),
        "es_acreditable": False,
        "es_retencion_definitiva": True,
        "requiere_autorizacion_sat": False
    },
    {
        "regimen_codigo": "PC_FEL",
        "impuesto_codigo": "ISR",
        "tasa_porcentaje": Decimal("4.00"),
        "limite_superior": Decimal("300000.00"),
        "es_acreditable": False,
        "es_retencion_definitiva": True,
        "requiere_autorizacion_sat": False
    },
    # --- RÉGIMEN GENERAL SOBRE UTILIDADES ---
    {
        "regimen_codigo": "RG_UTILIDADES",
        "impuesto_codigo": "IVA_GENERAL",
        "tasa_porcentaje": Decimal("12.00"),
        "es_acreditable": True,
        "es_retencion_definitiva": False,
        "requiere_autorizacion_sat": False
    },
    {
        "regimen_codigo": "RG_UTILIDADES",
        "impuesto_codigo": "ISR",
        "tasa_porcentaje": Decimal("25.00"),
        "es_acreditable": False,
        "es_retencion_definitiva": False,
        "requiere_autorizacion_sat": False
    },
    {
        "regimen_codigo": "RG_UTILIDADES",
        "impuesto_codigo": "ISO",
        "tasa_porcentaje": Decimal("1.00"),
        "es_acreditable": True,
        "es_retencion_definitiva": False,
        "requiere_autorizacion_sat": False
    },
    # --- RÉGIMEN OPCIONAL SIMPLIFICADO (ROS) ---
    # Nota: Se guarda el Tramo 1 como base. El backend debe aplicar la lógica 
    # progresiva (7% + 1500) cuando los ingresos superen el limite_superior.
    {
        "regimen_codigo": "ROS",
        "impuesto_codigo": "ISR",
        "tasa_porcentaje": Decimal("5.00"),
        "tasa_fija_monto": Decimal("0.00"),
        "limite_inferior": Decimal("0.01"),
        "limite_superior": Decimal("30000.00"),
        "es_acreditable": False,
        "es_retencion_definitiva": True,
        "requiere_autorizacion_sat": False
    },
]