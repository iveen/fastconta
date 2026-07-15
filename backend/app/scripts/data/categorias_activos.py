"""
Catálogo de Categorías de Activos Fijos
Basado en el Artículo 28 del Decreto 10-2012 (Ley de Actualización Tributaria de Guatemala)
Define las tasas de depreciación aceptadas fiscalmente y vida útil por categoría.
"""
from decimal import Decimal

CATEGORIAS_ACTIVOS_FIJOS = [
    {
        "nombre": "Edificios y Construcciones",
        "codigo_prefijo": "EDIF",
        "descripcion": "Edificios, construcciones e instalaciones adheridas a los inmuebles y sus mejoras. (Art. 28, numeral 1, Dec. 10-2012)",
        "tasa_minima_anual": Decimal("0.00"),
        "tasa_maxima_anual": Decimal("5.00"),
        "vida_util_meses_default": 240
    },
    {
        "nombre": "Plantaciones Agrícolas",
        "codigo_prefijo": "PLAN",
        "descripcion": "Árboles, arbustos, frutales y especies vegetales que produzcan frutos o productos que generen rentas gravadas. (Art. 28, numeral 2, Dec. 10-2012)",
        "tasa_minima_anual": Decimal("0.00"),
        "tasa_maxima_anual": Decimal("15.00"),
        "vida_util_meses_default": 80
    },
    {
        "nombre": "Mobiliario y Equipo de Oficina",
        "codigo_prefijo": "MOB",
        "descripcion": "Instalaciones no adheridas a los inmuebles, mobiliario y equipo de oficina, buques-tanques, barcos y material ferroviario, marítimo, fluvial o lacustre. (Art. 28, numeral 3, Dec. 10-2012)",
        "tasa_minima_anual": Decimal("0.00"),
        "tasa_maxima_anual": Decimal("20.00"),
        "vida_util_meses_default": 60
    },
    {
        "nombre": "Maquinaria y Vehículos",
        "codigo_prefijo": "VEH",
        "descripcion": "Semovientes utilizados como animales de carga o de trabajo, maquinaria, vehículos en general, grúas, aviones, remolques, semirremolques, contenedores y material rodante. (Art. 28, numeral 4, Dec. 10-2012)",
        "tasa_minima_anual": Decimal("0.00"),
        "tasa_maxima_anual": Decimal("20.00"),
        "vida_util_meses_default": 60
    },
    {
        "nombre": "Equipo de Cómputo",
        "codigo_prefijo": "COMP",
        "descripcion": "Equipo de computación, incluyendo los programas (software). (Art. 28, numeral 5, Dec. 10-2012)",
        "tasa_minima_anual": Decimal("0.00"),
        "tasa_maxima_anual": Decimal("33.33"),
        "vida_util_meses_default": 36
    },
    {
        "nombre": "Herramientas y Utensilios",
        "codigo_prefijo": "HERR",
        "descripcion": "Herramientas, porcelana, cristalería, mantelería, cubiertos y similares. (Art. 28, numeral 6, Dec. 10-2012)",
        "tasa_minima_anual": Decimal("0.00"),
        "tasa_maxima_anual": Decimal("25.00"),
        "vida_util_meses_default": 48
    },
    {
        "nombre": "Ganado de Reproducción",
        "codigo_prefijo": "GAN",
        "descripcion": "Reproductores de raza, machos y hembras. La depreciación se calcula sobre el valor de costo de tales animales menos su valor como ganado común. (Art. 28, numeral 7, Dec. 10-2012)",
        "tasa_minima_anual": Decimal("0.00"),
        "tasa_maxima_anual": Decimal("25.00"),
        "vida_util_meses_default": 48
    },
    {
        "nombre": "Otros Bienes Muebles",
        "codigo_prefijo": "OTRO",
        "descripcion": "Para los bienes muebles no indicados en los incisos anteriores. (Art. 28, numeral 8, Dec. 10-2012)",
        "tasa_minima_anual": Decimal("0.00"),
        "tasa_maxima_anual": Decimal("10.00"),
        "vida_util_meses_default": 120
    },
    {
        "nombre": "Maquinaria y Equipo",
        "codigo_prefijo": "MAQ",
        "descripcion": "Maquinaria y equipo industrial, de manufactura, y demás bienes muebles no clasificados en otra categoría específica. (Art. 28, numeral 4, Dec. 10-2012)",
        "tasa_minima_anual": Decimal("0.00"),
        "tasa_maxima_anual": Decimal("10.00"),
        "vida_util_meses_default": 120
    },
]