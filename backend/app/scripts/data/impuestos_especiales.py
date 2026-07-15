"""
Catálogo de Impuestos Especiales de Guatemala
Estos impuestos NO son base para el cálculo del IVA (Art. 11 Ley 27-92)
y deben restarse del Gran Total de la factura.
"""

IMPUESTOS_ESPECIALES = [
    {
        "codigo": "PETROLEO",
        "nombre": "Petróleo",
        "descripcion": "Impuesto al Petróleo (Decreto 72-96)."
    },
    {
        "codigo": "TURISMO_HOSPEDAJE",
        "nombre": "Turismo Hospedaje",
        "descripcion": "Impuesto al Turismo por Hospedage (Decreto 37-2014)."
    },
    {
        "codigo": "TURISMO_PASAJES",
        "nombre": "Turismo Pasajes",
        "descripcion": "Impuesto al Turismo por Pasajes Aéreos."
    },
    {
        "codigo": "TIMBRE_PRENSA",
        "nombre": "Timbre de Prensa",
        "descripcion": "Impuesto de Timbre de Prensa (Ley de Imprenta)."
    },
    {
        "codigo": "BEBIDAS",
        "nombre": "Bebidas Alcohólicas",
        "descripcion": "Impuesto Específico a Bebidas Alcohólicas (Decreto 56-2013)."
    },
    {
        "codigo": "TABACO",
        "nombre": "Tabaco",
        "descripcion": "Impuesto Específico a Productos de Tabaco (Decreto 56-2013)."
    },
    {
        "codigo": "CEMENTO",
        "nombre": "Cemento",
        "descripcion": "Impuesto Específico al Cemento (Decreto 56-2013)."
    },
    {
        "codigo": "VEHICULOS_IPRIMA",
        "nombre": "Vehículos (IPRIMA)",
        "descripcion": "Impuesto a la Primera Matrícula de Vehículos (Decreto 91-97)."
    },
]