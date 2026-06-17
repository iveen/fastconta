import asyncio
import logging

from sqlalchemy import select

# Ajusta estos imports según la estructura real de tu proyecto
from app.models.global_models import CasillaSat, FormularioSat

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==============================================================================
# DATOS DEL FORMULARIO SAT-2237
# ==============================================================================
FORMULARIO_DATA = {
    "codigo": "SAT-2237",
    "nombre": "IVA GENERAL - Régimen General (Operaciones Locales y Exportación)",
    "descripcion": "Declaración Jurada y Pago Mensual. Contribuyentes que realizan operaciones locales y de exportación."
}

# Lista de casillas basadas en el Excel proporcionado.
# Los 'codigo' coinciden EXACTAMENTE con las claves del MAPA_CALCULO_SAT_2237 en el servicio.
CASILLAS_DATA = [
    # --- SECCIÓN 3: DÉBITO FISCAL POR OPERACIONES LOCALES ---
    {"seccion": "3", "codigo": "VENTAS_EXENTAS_LOCALES", "nombre": "Ventas exentas y servicios exentos", "tipo_valor": "BASE", "orden": 1},
    {"seccion": "3", "codigo": "VENTAS_MEDICAMENTOS_EXENTOS", "nombre": "Ventas de medicamentos genéricos, alternativos y antirretrovirales", "tipo_valor": "BASE", "orden": 2},
    {"seccion": "3", "codigo": "VENTAS_VEHICULOS_ANTIGUOS", "nombre": "Ventas de vehículos terrestres del modelo de dos años o más anteriores", "tipo_valor": "BASE", "orden": 3},
    {"seccion": "3", "codigo": "VENTAS_VEHICULOS_RECIENTES", "nombre": "Ventas de vehículos terrestres del modelo del año en curso, siguiente o anterior", "tipo_valor": "DEBITO", "orden": 4},
    {"seccion": "3", "codigo": "VENTAS_GRAVADAS_LOCALES", "nombre": "Ventas gravadas", "tipo_valor": "DEBITO", "orden": 5},
    {"seccion": "3", "codigo": "SERVICIOS_GRAVADOS_LOCALES", "nombre": "Servicios gravados", "tipo_valor": "DEBITO", "orden": 6},
    
    # --- SECCIÓN 5: CRÉDITO FISCAL POR OPERACIONES LOCALES ---
    {"seccion": "5", "codigo": "COMPRAS_MEDICAMENTOS_EXENTOS", "nombre": "Compras de medicamentos genéricos, alternativos y antirretrovirales", "tipo_valor": "CREDITO", "orden": 10},
    {"seccion": "5", "codigo": "COMPRAS_PEQUENO_CONTRIBUYENTE", "nombre": "Compras y servicios adquiridos de pequeños contribuyentes", "tipo_valor": "CREDITO", "orden": 11},
    {"seccion": "5", "codigo": "COMPRAS_VEHICULOS_ANTIGUOS", "nombre": "Compras de vehículos terrestres del modelo de dos años o más anteriores", "tipo_valor": "BASE", "orden": 12},
    {"seccion": "5", "codigo": "COMPRAS_VEHICULOS_RECIENTES", "nombre": "Compras de vehículos terrestres del modelo del año en curso, siguiente o anterior", "tipo_valor": "CREDITO", "orden": 13},
    {"seccion": "5", "codigo": "COMPRAS_COMBUSTIBLES_LOCALES", "nombre": "Compras de combustibles", "tipo_valor": "CREDITO", "orden": 14},
    {"seccion": "5", "codigo": "OTRAS_COMPRAS_LOCALES", "nombre": "Otras Compras", "tipo_valor": "CREDITO", "orden": 15},
    {"seccion": "5", "codigo": "SERVICIOS_ADQUIRIDOS_LOCALES", "nombre": "Servicios adquiridos", "tipo_valor": "CREDITO", "orden": 16},
    {"seccion": "5", "codigo": "IMPORTACIONES_CENTROAMERICA", "nombre": "Importaciones de Centro América", "tipo_valor": "CREDITO", "orden": 17},
    {"seccion": "5", "codigo": "IMPORTACIONES_RESTO_MUNDO", "nombre": "Importaciones del resto del mundo", "tipo_valor": "CREDITO", "orden": 18},
    {"seccion": "5", "codigo": "COMPRAS_ACTIVO_FIJO_LOCALES", "nombre": "Compras de activos fijos directamente vinculados con el proceso productivo", "tipo_valor": "CREDITO", "orden": 19},
    {"seccion": "5", "codigo": "REMANENTE_CREDITO_FISCAL_ANTERIOR", "nombre": "Remanente de crédito fiscal del período anterior", "tipo_valor": "CREDITO", "orden": 20},

    # --- SECCIÓN 7: DETERMINACIÓN (Calculados por el servicio, pero útiles para mostrar) ---
    {"seccion": "7", "codigo": "IMPUESTO_TOTAL_DETERMINADO_LOCAL", "nombre": "IMPUESTO TOTAL DETERMINADO (Débitos mayor que créditos) Operaciones locales", "tipo_valor": "CALCULADO", "orden": 30},
    {"seccion": "7", "codigo": "CREDITO_FISCAL_PERIODO_SIGUIENTE_LOCAL", "nombre": "Crédito fiscal para el período siguiente por operaciones locales", "tipo_valor": "CALCULADO", "orden": 31},
    {"seccion": "7", "codigo": "IMPUESTO_A_PAGAR", "nombre": "IMPUESTO A PAGAR", "tipo_valor": "CALCULADO", "orden": 32},
    {"seccion": "7", "codigo": "RETENCIONES_IVA_RECIBIDAS", "nombre": "(-) Retenciones de IVA practicadas en el período", "tipo_valor": "RETENCION", "orden": 33},

    # --- SECCIÓN 9: INDICADORES COMERCIALES ---
    {"seccion": "9", "codigo": "INDICADOR_CANTIDAD_FACTURAS_EMITIDAS", "nombre": "Facturas Emitidas (incluye anuladas)", "tipo_valor": "INDICADOR", "orden": 40},
    {"seccion": "9", "codigo": "INDICADOR_CANTIDAD_FACTURAS_RECIBIDAS", "nombre": "Facturas Recibidas", "tipo_valor": "INDICADOR", "orden": 41},
    {"seccion": "9", "codigo": "INDICADOR_CANTIDAD_NC_EMITIDAS", "nombre": "Notas de Crédito Emitidas", "tipo_valor": "INDICADOR", "orden": 42},
    {"seccion": "9", "codigo": "INDICADOR_CANTIDAD_ND_EMITIDAS", "nombre": "Notas de Débito Emitidas", "tipo_valor": "INDICADOR", "orden": 43},
]


async def seed_sat_2237():
    """
    Pobla el catálogo global con la estructura del formulario SAT-2237.
    Es idempotente: si ya existe, no hace nada.
    """
    logger.info("🚀 Iniciando seed del catálogo SAT-2237...")
    
    # Obtener la sesión de base de datos (ajusta esto a tu forma de obtener la sesión global)
    # Si tienes un get_public_db que es un generator, úsalo así:
    from app.db.session import (
        AsyncSessionLocal,  # Asumiendo que tienes esto configurado
    )
    async with AsyncSessionLocal() as db:
        try:
            # 1. Verificar o crear el Formulario
            stmt_form = select(FormularioSat).where(FormularioSat.codigo == FORMULARIO_DATA["codigo"])
            result = await db.execute(stmt_form)
            formulario = result.scalar_one_or_none()

            if not formulario:
                formulario = FormularioSat(**FORMULARIO_DATA)
                db.add(formulario)
                await db.flush() # Para obtener el ID del formulario
                logger.info(f"✅ Formulario {FORMULARIO_DATA['codigo']} creado.")
            else:
                logger.info(f"ℹ️ Formulario {FORMULARIO_DATA['codigo']} ya existe.")

            # 2. Verificar o crear las Casillas
            casillas_existentes_stmt = select(CasillaSat.codigo).where(CasillaSat.formulario_id == formulario.id)
            result_casillas = await db.execute(casillas_existentes_stmt)
            codigos_existentes = {row[0] for row in result_casillas.fetchall()}

            casillas_a_crear = []
            for data in CASILLAS_DATA:
                if data["codigo"] not in codigos_existentes:
                    casillas_a_crear.append(CasillaSat(
                        formulario_id=formulario.id,
                        **data
                    ))

            if casillas_a_crear:
                db.add_all(casillas_a_crear)
                await db.commit()
                logger.info(f"✅ Se crearon {len(casillas_a_crear)} casillas nuevas para el SAT-2237.")
            else:
                logger.info("ℹ️ Todas las casillas del SAT-2237 ya están registradas.")

            logger.info("🎉 Seed del SAT-2237 completado exitosamente.")

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Error durante el seed: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(seed_sat_2237())