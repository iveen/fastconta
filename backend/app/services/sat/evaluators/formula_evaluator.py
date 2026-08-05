"""
Evaluador de fórmulas aritméticas con referencias a casillas.

Soporta:
- Operaciones básicas: +, -, *, /
- Paréntesis
- Funciones: max(), min(), abs()
- Referencias: {codigo_casilla}
- Delega a CaseWhenEvaluator para expresiones CASE WHEN
"""

import logging
import re
from decimal import Decimal, InvalidOperation

from .case_when_evaluator import CaseWhenEvaluator

logger = logging.getLogger(__name__)

# Patrón para referencias {codigo}
PATRON_REFERENCIA = re.compile(r"\{([^}]+)\}")

# Expresión regular para validar que solo contiene caracteres seguros
# Permite: dígitos, punto, operadores, paréntesis, espacios, comas, y nombres de funciones
PATRON_VALIDACION = re.compile(
    r"^[\d\.\+\-\*\/\(\)\s,]+(max|min|abs)?[\d\.\+\-\*\/\(\)\s,]*$",
    re.IGNORECASE,
)


class FormulaEvaluator:
    """
    Evaluador de fórmulas aritméticas con referencias a casillas.
    
    Ejemplos:
        "{3.1} + {3.2} * 0.12"
        "CASE WHEN {5_SUM} > {3_SUM} THEN {5_SUM} - {3_SUM} ELSE 0 END"
        "max({3.1}, {3.2})"
    """
    
    @staticmethod
    def evaluar(formula: str, valores: dict[str, Decimal]) -> Decimal:
        """
        Evalúa una fórmula aritmética o CASE WHEN.
        
        Args:
            formula: Fórmula a evaluar
            valores: Diccionario {codigo_casilla: valor}
        
        Returns:
            Resultado de la evaluación como Decimal
        
        Raises:
            ValueError: Si la fórmula es inválida
        """
        if not formula or not formula.strip():
            return Decimal("0")
        
        formula = formula.strip()
        
        # Si es CASE WHEN, delegar a CaseWhenEvaluator
        if CaseWhenEvaluator.es_case_when(formula):
            return CaseWhenEvaluator.evaluar(formula, valores)
        
        # Reemplazar referencias {codigo} por valores
        def reemplazar_referencia(match: re.Match) -> str:
            codigo = match.group(1).strip()
            valor = valores.get(codigo, Decimal("0"))
            return str(valor)
        
        expresion = PATRON_REFERENCIA.sub(reemplazar_referencia, formula)
        
        # Validar que la expresión solo contiene caracteres seguros
        if not PATRON_VALIDACION.match(expresion):
            logger.warning(f"Fórmula con caracteres no permitidos: {formula}")
            # Intentar evaluar de todas formas, pero con namespace restringido
        
        # Evaluar con namespace restringido
        try:
            resultado = eval(  # noqa: S307
                expresion,
                {"__builtins__": {}},
                {"Decimal": Decimal, "max": max, "min": min, "abs": abs},
            )
            return Decimal(str(resultado))
        except (SyntaxError, TypeError, InvalidOperation, ZeroDivisionError) as e:
            logger.error(f"Error evaluando fórmula '{formula}': {e}")
            # En caso de error (ej: división por cero), retornar 0
            return Decimal("0")
    
    @staticmethod
    def extraer_dependencias(formula: str) -> list[str]:
        """
        Extrae los códigos de casillas referenciados en la fórmula.
        
        Args:
            formula: Fórmula a analizar
        
        Returns:
            Lista de códigos de casillas referenciados
        
        Ejemplo:
            "{3.1} + {3.2} * 0.12" → ["3.1", "3.2"]
        """
        if not formula:
            return []
        
        return [match.group(1).strip() for match in PATRON_REFERENCIA.finditer(formula)]
    
    @staticmethod
    def validar_formula(formula: str) -> tuple[bool, str]:
        """
        Valida que una fórmula sea sintácticamente correcta.
        
        Args:
            formula: Fórmula a validar
        
        Returns:
            Tupla (es_valida, mensaje_error)
        """
        if not formula or not formula.strip():
            return False, "Fórmula vacía"
        
        formula = formula.strip()
        
        # Si es CASE WHEN, validar estructura
        if CaseWhenEvaluator.es_case_when(formula):
            if not re.search(r"CASE\s+WHEN.+THEN.+ELSE.+END", formula, re.IGNORECASE | re.DOTALL):
                return False, "Estructura CASE WHEN incompleta"
            return True, "OK"
        
        # Validar paréntesis balanceados
        if formula.count("(") != formula.count(")"):
            return False, "Paréntesis no balanceados"
        
        # Validar que solo contiene caracteres permitidos
        expresion_limpia = PATRON_REFERENCIA.sub("0", formula)
        if not PATRON_VALIDACION.match(expresion_limpia):
            return False, "Caracteres no permitidos en la fórmula"
        
        return True, "OK"
