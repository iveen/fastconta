"""
Catálogo Base de Impuestos de Guatemala
Incluye los impuestos principales que aplican a la mayoría de contribuyentes.
Los impuestos especiales (petróleo, bebidas, tabaco, etc.) se manejan en
el catálogo separado CatalogoImpuestoEspecial.
"""
from decimal import Decimal

IMPUESTOS = [
    {
        "codigo": "IVA_GENERAL",
        "nombre": "Impuesto al Valor Agregado",
        "descripcion": "Art. 10 Ley 27-92. Tasa general del 12% sobre operaciones gravadas.",
        "tasa_porcentaje": Decimal("12.00"),
        "tasa_fija_monto": Decimal("0.00"),
        "limite_inferior": Decimal("0.00"),
        "limite_superior": None,
        "frecuencia_pago": "MENSUAL",
        "frecuencia_liquidacion": "MENSUAL"
    },
    {
        "codigo": "IVA_EXENTO",
        "nombre": "IVA - Operaciones Exentas",
        "descripcion": "Art. 7 Ley 27-92. Operaciones exentas del IVA (alimentos básicos, servicios médicos, educación, etc.).",
        "tasa_porcentaje": Decimal("0.00"),
        "tasa_fija_monto": Decimal("0.00"),
        "limite_inferior": Decimal("0.00"),
        "limite_superior": None,
        "frecuencia_pago": "MENSUAL",
        "frecuencia_liquidacion": "MENSUAL"
    },
    {
        "codigo": "ISR",
        "nombre": "Impuesto sobre la Renta",
        "descripcion": "Art. 36 Ley 26-92 / Art. 44-46 Ley 10-2012. Variable según régimen (PC 5%/4%, ROS 5%, Sobre Utilidades 25%, etc.).",
        "tasa_porcentaje": None,
        "tasa_fija_monto": Decimal("0.00"),
        "limite_inferior": Decimal("0.00"),
        "limite_superior": None,
        "frecuencia_pago": "VARIABLE",
        "frecuencia_liquidacion": "ANUAL"
    },
    {
        "codigo": "ISO",
        "nombre": "Impuesto de Solidaridad",
        "descripcion": "Art. 7 Ley 73-2008. 1% sobre Activos Netos o Ingresos Brutos (el que sea mayor). Crédito contra ISR.",
        "tasa_porcentaje": Decimal("1.00"),
        "tasa_fija_monto": Decimal("0.00"),
        "limite_inferior": Decimal("0.00"),
        "limite_superior": None,
        "frecuencia_pago": "TRIMESTRAL",
        "frecuencia_liquidacion": "ANUAL"
    },
]