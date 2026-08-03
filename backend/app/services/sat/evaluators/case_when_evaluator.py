"""
Evaluador de expresiones CASE WHEN (sintaxis SQL).

Convierte expresiones tipo:
  CASE WHEN {5_SUM} > {3_SUM} THEN {5_SUM} - {3_SUM} ELSE 0 END

A expresiones Python equivalentes:
  ({5_SUM} - {3_SUM}) if ({5_SUM} > {3_SUM}) else 0
"""

import logging
import re
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)

# Patrón para detectar CASE WHEN
PATRON_CASE_WHEN = re.compile(
    r"CASE\s+WHEN\s+(.+?)\s+THEN\s+(.+?)\s+ELSE\s+(.+?)\s+END",
    re.IGNORECASE | re.DOTALL,
)

# Patrón para referencias {codigo}
PATRON_REFERENCIA = re.compile(r"\{([^}]+)\}")


class CaseWhenEvaluator:
    """
    Evaluador de expresiones CASE WHEN.
    
    Convierte sintaxis SQL a Python y evalúa de forma segura.
    """
    
    @staticmethod
    def es_case_when(formula: str) -> bool:
        """Verifica si la fórmula contiene una expresión CASE WHEN."""
        return bool(PATRON_CASE_WHEN.search(formula))
    
    @staticmethod
    def evaluar(formula: str, valores: dict[str, Decimal]) -> Decimal:
        """
        Evalúa una expresión CASE WHEN.
        
        Args:
            formula: Fórmula con sintaxis CASE WHEN
            valores: Diccionario {codigo_casilla: valor}
        
        Returns:
            Resultado de la evaluación como Decimal
        
        Raises:
            ValueError: Si la fórmula es inválida
        """
        if not CaseWhenEvaluator.es_case_when(formula):
            raise ValueError(f"La fórmula no es una expresión CASE WHEN: {formula}")
        
        # Reemplazar referencias {codigo} por valores
        def reemplazar_referencia(match: re.Match) -> str:
            codigo = match.group(1).strip()
            valor = valores.get(codigo, Decimal("0"))
            return str(valor)
        
        formula_resuelta = PATRON_REFERENCIA.sub(reemplazar_referencia, formula)
        
        # Convertir CASE WHEN a expresión Python
        def convertir_case_when(match: re.Match) -> str:
            condicion = match.group(1).strip()
            valor_si = match.group(2).strip()
            valor_no = match.group(3).strip()
            
            # Sanitizar operadores SQL a Python
            condicion_py = condicion.replace("=", "==")
            
            return f"(({valor_si}) if ({condicion_py}) else ({valor_no}))"
        
        expresion_python = PATRON_CASE_WHEN.sub(convertir_case_when, formula_resuelta)
        
        # Evaluar con namespace restringido
        try:
            resultado = eval(  # noqa: S307
                expresion_python,
                {"__builtins__": {}},
                {"Decimal": Decimal, "max": max, "min": min, "abs": abs},
            )
            return Decimal(str(resultado))
        except (SyntaxError, TypeError, InvalidOperation) as e:
            logger.error(f"Error evaluando CASE WHEN '{formula}': {e}")
            raise ValueError(f"Error evaluando CASE WHEN: {e}") from e
    
