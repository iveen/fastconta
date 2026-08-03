"""
Estrategia específica para el formulario SAT-2237 (IVA General).

Encapsula la lógica particular del Régimen Opcional Mensual:
- Carga remanente del período anterior
- Calcula totales de débito y crédito fiscal
- Determina impuesto a pagar y remanente siguiente
- Clasifica valores según tipo_casilla
"""

import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.global_models import FormularioSat
from app.models.tenant_models import DeclaracionImpuesto

from .base import FormularioCalculoStrategy
from .registry import registrar

logger = logging.getLogger(__name__)


def redondear_entero(valor: Decimal | float | int | None) -> int:
    """Redondea a entero (el formulario SAT usa Q enteros)."""
    from decimal import ROUND_HALF_UP, InvalidOperation
    if valor is None:
        return 0
    try:
        return int(Decimal(str(valor)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except (InvalidOperation, ValueError):
        return 0


@registrar("SAT-2237")
class SAT2237Strategy(FormularioCalculoStrategy):
    """
    IVA General - Régimen Opcional Mensual.
    
    Lógica específica:
    - Sección 3: Débito Fiscal (ventas locales gravadas)
    - Sección 4: Exportaciones (referencia, no genera IVA)
    - Sección 5: Crédito Fiscal Local
    - Sección 6: Crédito Fiscal Exportaciones
    - Sección 7: Determinación del impuesto
    - Sección 8: Indicadores comerciales
    - Sección 9.1/9.2: Conteos y montos informativos
    - Sección 10: Rectificación
    - Sección 11: Accesorios (multas, intereses)
    """
    
    codigo_formulario = "SAT-2237"
    
    async def preparar_contexto(
        self, db: AsyncSession, empresa_id: int, anio: int, mes: int
    ) -> dict:
        """
        Carga el remanente de crédito fiscal del período anterior.
        
        El remanente se arrastra desde la declaración FINALIZADA del mes anterior.
        Si no hay declaración anterior o no tiene remanente, retorna 0.
        """
        # 1. Obtener el formulario SAT-2237 activo
        stmt_form = select(FormularioSat).where(
            FormularioSat.codigo == self.codigo_formulario,
            FormularioSat.es_version_activa.is_(True),
        )
        formulario = (await db.execute(stmt_form)).scalar_one_or_none()
        
        if formulario is None:
            logger.warning(
                f"Formulario {self.codigo_formulario} no encontrado. "
                "El remanente anterior será 0."
            )
            return {"formulario_id": None, "remanente_anterior": Decimal("0")}
        
        # 2. Calcular período anterior
        mes_ant = mes - 1 if mes > 1 else 12
        anio_ant = anio if mes > 1 else anio - 1
        
        # 3. Buscar remanente de la declaración FINALIZADA del período anterior
        stmt_rem = select(DeclaracionImpuesto.remanente_siguiente_periodo).where(
            DeclaracionImpuesto.empresa_id == empresa_id,
            DeclaracionImpuesto.formulario_sat_id == formulario.id,
            DeclaracionImpuesto.anio == anio_ant,
            DeclaracionImpuesto.mes == mes_ant,
            DeclaracionImpuesto.estado == "FINALIZADO",
        )
        remanente_val = (await db.execute(stmt_rem)).scalar_one_or_none()
        
        remanente = Decimal(str(remanente_val)) if remanente_val else Decimal("0")
        
        logger.info(
            f"SAT-2237: Remanente anterior (período {anio_ant}-{mes_ant:02d}): "
            f"Q {remanente}"
        )
        
        return {
            "formulario_id": formulario.id,
            "remanente_anterior": remanente,
            "periodo_anterior": f"{anio_ant}-{mes_ant:02d}",
        }
    
    def calcular_totales_cabecera(
        self, valores: dict[str, Decimal], contexto: dict
    ) -> dict[str, int]:
        """
        Calcula los totales que van en la cabecera de DeclaracionImpuesto.
        
        Para el SAT-2237:
        - total_debito_fiscal: suma de casillas tipo DEBITO_FISCAL
        - total_credito_fiscal: suma de casillas tipo CREDITO_FISCAL
        - impuesto_determinado: max(0, debito - credito - remanente)
        - remanente_siguiente: max(0, credito + remanente - debito)
        - impuesto_a_pagar: valor de la casilla 11_TOTAL (o 7_PAGAR)
        """
        # Nota: los valores ya vienen clasificados por el motor
        # (base_imponible o monto_impuesto según tipo_casilla)
        
        # Para el SAT-2237, los totales de débito y crédito se calculan
        # sumando las casillas CALCULADO de las secciones correspondientes:
        # - 3_SUM: sumatoria de bases y débitos de sección 3
        # - 5_SUM: sumatoria de créditos de sección 5
        # - 6_TOTAL: total de créditos de sección 6
        # - 4_TOTAL: total de débitos de sección 4 (exportaciones)
        
        # Sin embargo, el motor ya calculó estos valores mediante fórmulas.
        # La estrategia solo necesita extraerlos del diccionario de valores.
        
        # Totales de las secciones (ya calculados por fórmulas)
        total_debito_local = valores.get("3_SUM", Decimal("0"))
        total_credito_local = valores.get("5_SUM", Decimal("0"))
        total_debito_export = valores.get("4_TOTAL", Decimal("0"))
        total_credito_export = valores.get("6_TOTAL", Decimal("0"))
        
        # Totales generales
        total_debito = total_debito_local + total_debito_export
        total_credito = total_credito_local + total_credito_export
        
        # Remanente del período anterior
        remanente = contexto.get("remanente_anterior", Decimal("0"))
        
        # Impuesto determinado (solo si débito > crédito)
        impuesto_determinado = max(Decimal("0"), total_debito - total_credito - remanente)
        
        # Remanente para el siguiente período (si crédito > débito)
        remanente_siguiente = max(
            Decimal("0"),
            total_credito + remanente - total_debito,
        )
        
        # Impuesto a pagar: casilla 11_TOTAL (incluye accesorios)
        # Si no existe, usar 7_PAGAR (solo impuesto sin accesorios)
        impuesto_a_pagar = valores.get("11_TOTAL", valores.get("7_PAGAR", Decimal("0")))
        
        logger.info(
            f"SAT-2237 totales: Débito={total_debito}, Crédito={total_credito}, "
            f"Remanente ant={remanente}, Impuesto det={impuesto_determinado}, "
            f"Remanente sig={remanente_siguiente}, A pagar={impuesto_a_pagar}"
        )
        
        return {
            "total_debito_fiscal": redondear_entero(total_debito),
            "total_credito_fiscal": redondear_entero(total_credito),
            "remanente_periodo_anterior": redondear_entero(remanente),
            "impuesto_determinado": redondear_entero(impuesto_determinado),
            "remanente_siguiente_periodo": redondear_entero(remanente_siguiente),
            "impuesto_a_pagar": redondear_entero(impuesto_a_pagar),
        }
    
    def clasificar_valor_casilla(
        self, tipo_casilla: str, valor: Decimal
    ) -> tuple[Decimal, Decimal]:
        """
        Decide si un valor va en base_imponible o monto_impuesto.
        
        Para el SAT-2237:
        - BASE_IMPONIBLE, REFERENCIA, CONTEO → van en base_imponible
        - DEBITO_FISCAL, CREDITO_FISCAL, CALCULADO, AJUSTE, REMANENTE → van en monto_impuesto
        """
        tipo = (tipo_casilla or "").upper()
        
        if tipo in ("BASE_IMPONIBLE", "REFERENCIA", "CONTEO"):
            return valor, Decimal("0")
        
        # Todos los demás tipos van en monto_impuesto
        return Decimal("0"), valor
    
    def aplicar_logica_post_calculo(
        self, db: AsyncSession, declaracion, valores: dict, contexto: dict
    ) -> None:
        """
        Hook para lógica adicional post-cálculo.
        
        Para el SAT-2237, no se necesita lógica adicional porque:
        - Las fórmulas CASE WHEN ya calculan 7.1, 7.2, 7.3, 7.4
        - Los totales de cabecera ya se calcularon en calcular_totales_cabecera()
        - Los accesorios (sección 11) son casillas editables que el usuario completa
        
        Este hook queda disponible para futuros formularios que necesiten
        lógica adicional (ej: ISR progresivo, retenciones, etc.)
        """
        pass
