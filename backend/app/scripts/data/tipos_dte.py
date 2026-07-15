"""
Catálogo de Tipos de Documentos Tributarios Electrónicos (DTE) - SAT Guatemala
Incluye todos los tipos oficiales según el libro D de FEL.
"""

TIPOS_DTE = [
    {
        "codigo": "FACT",
        "descripcion": "Factura Electrónica",
        "requiere_complemento": False,
        "es_factura": True,
        "is_active": True
    },
    {
        "codigo": "FPEQ",
        "descripcion": "Factura Pequeño Contribuyente",
        "requiere_complemento": False,
        "es_factura": True,
        "is_active": True
    },
    {
        "codigo": "FAPE",
        "descripcion": "Factura Pequeño Contribuyente Régimen Electrónico",
        "requiere_complemento": False,
        "es_factura": True,
        "is_active": True
    },
    {
        "codigo": "FESP",
        "descripcion": "Factura Especial",
        "requiere_complemento": True,
        "es_factura": True,
        "is_active": True
    },
    {
        "codigo": "FEPE",
        "descripcion": "Factura Específica",
        "requiere_complemento": False,
        "es_factura": True,
        "is_active": True
    },
    {
        "codigo": "FACP",
        "descripcion": "Factura Provisional",
        "requiere_complemento": False,
        "es_factura": True,
        "is_active": True
    },
    {
        "codigo": "FACA",
        "descripcion": "Factura Contribuyente Agropecuario",
        "requiere_complemento": False,
        "es_factura": True,
        "is_active": True
    },
    {
        "codigo": "FAAE",
        "descripcion": "Factura Agropecuario Régimen Electrónico Especial",
        "requiere_complemento": False,
        "es_factura": True,
        "is_active": True
    },
    {
        "codigo": "FARP",
        "descripcion": "Factura Contribuyente Régimen Primario",
        "requiere_complemento": False,
        "es_factura": True,
        "is_active": True
    },
    {
        "codigo": "FPEC",
        "descripcion": "Factura Contribuyente Régimen Pecuario",
        "requiere_complemento": False,
        "es_factura": True,
        "is_active": True
    },
    {
        "codigo": "FCAM",
        "descripcion": "Factura Cambiaria",
        "requiere_complemento": False,
        "es_factura": True,
        "is_active": True
    },
    {
        "codigo": "FCAP",
        "descripcion": "Factura Cambiaria Pequeño Contribuyente",
        "requiere_complemento": False,
        "es_factura": True,
        "is_active": True
    },
    {
        "codigo": "FCCA",
        "descripcion": "Factura Cambiaria Contribuyente Agropecuario",
        "requiere_complemento": False,
        "es_factura": True,
        "is_active": True
    },
    {
        "codigo": "FCRP",
        "descripcion": "Factura Cambiaria Contribuyente Régimen Primario",
        "requiere_complemento": False,
        "es_factura": True,
        "is_active": True
    },
    {
        "codigo": "FCAE",
        "descripcion": "Factura Cambiaria Agropecuario Régimen Electrónico Especial",
        "requiere_complemento": False,
        "es_factura": True,
        "is_active": True
    },
    {
        "codigo": "FCPC",
        "descripcion": "Factura Cambiaria Contribuyente Régimen Pecuario",
        "requiere_complemento": False,
        "es_factura": True,
        "is_active": True
    },
    {
        "codigo": "NCRE",
        "descripcion": "Nota de Crédito",
        "requiere_complemento": True,
        "es_factura": False,
        "is_active": True
    },
    {
        "codigo": "NDEB",
        "descripcion": "Nota de Débito",
        "requiere_complemento": True,
        "es_factura": False,
        "is_active": True
    },
    {
        "codigo": "NABN",
        "descripcion": "Nota de Abono",
        "requiere_complemento": True,
        "es_factura": False,
        "is_active": True
    },
    {
        "codigo": "NEV",
        "descripcion": "Nota de Envío",
        "requiere_complemento": False,
        "es_factura": False,
        "is_active": True
    },
    {
        "codigo": "RECI",
        "descripcion": "Recibo",
        "requiere_complemento": False,
        "es_factura": False,
        "is_active": True
    },
    {
        "codigo": "RANT",
        "descripcion": "Recibo de Anticipo",
        "requiere_complemento": False,
        "es_factura": False,
        "is_active": True
    },
    {
        "codigo": "RDON",
        "descripcion": "Recibo de Donación",
        "requiere_complemento": False,
        "es_factura": False,
        "is_active": True
    },
    {
        "codigo": "CAIS",
        "descripcion": "Constancia de Adquisición de Insumos y Servicios",
        "requiere_complemento": False,
        "es_factura": False,
        "is_active": True
    },
    {
        "codigo": "CIVA",
        "descripcion": "Constancia de Exención de IVA",
        "requiere_complemento": False,
        "es_factura": False,
        "is_active": True
    },
]