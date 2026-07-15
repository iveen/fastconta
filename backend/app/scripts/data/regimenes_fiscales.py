"""
Catálogo de Regímenes Fiscales de Guatemala (SAT)
"""

REGIMENES_FISCALES = [
    {
        "codigo": "PC_MANUAL",
        "nombre": "Pequeño Contribuyente Manual",
        "descripcion": "5% mensual sobre ingresos brutos. No genera crédito fiscal. (Art. 45 Dec. 10-2012)"
    },
    {
        "codigo": "PC_FEL",
        "nombre": "Pequeño Contribuyente Electrónico (FEL)",
        "descripcion": "4% mensual sobre ingresos brutos. No genera crédito fiscal. (Art. 45 Dec. 10-2012)"
    },
    {
        "codigo": "RG_UTILIDADES",
        "nombre": "Régimen General Sobre Utilidades",
        "descripcion": "25% sobre la renta neta anual. Obligado a llevar contabilidad completa."
    },
    {
        "codigo": "ROS",
        "nombre": "Régimen Opcional Simplificado",
        "descripcion": "5% sobre ingresos brutos mensuales. Opcional para pequeños contribuyentes que cumplan requisitos."
    },
    {
        "codigo": "ESPECIFICO",
        "nombre": "Régimen Específico",
        "descripcion": "Aplicable a actividades económicas específicas definidas por la SAT con tarifas particulares."
    },
    {
        "codigo": "EXPORTACION",
        "nombre": "Régimen de Exportación",
        "descripcion": "Exento de IVA para bienes y servicios destinados a la exportación definitiva."
    },
    {
        "codigo": "AGROPECUARIO",
        "nombre": "Régimen Especial Agropecuario",
        "descripcion": "Beneficios y tratamientos fiscales específicos para actividades agropecuarias primarias."
    },
    {
        "codigo": "RENTA_TRABAJO",
        "nombre": "Rentas del Trabajo",
        "descripcion": "Sujeto a retención en la fuente sobre salarios, prestaciones y demás ingresos laborales."
    },
    {
        "codigo": "NO_RESIDENTES",
        "nombre": "Retención a No Residentes",
        "descripcion": "Aplicación de retenciones a ingresos de fuente guatemalteca percibidos por no residentes."
    }
]