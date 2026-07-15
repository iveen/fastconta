"""
Catálogo de Estados de Libro contable
Define los estados por los que pasa un libro en su ciclo de vida:
desde borrador hasta aceptación/rechazo por la SAT.
"""

ESTADOS_LIBRO = [
    {
        "nombre": "Borrador",
    },
    {
        "nombre": "Generado",
    },
    {
        "nombre": "Enviado",
    },
    {
        "nombre": "Aceptado",
    },
    {
        "nombre": "Rechazado",
    },
]