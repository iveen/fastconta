"""
Evaluadores de fórmulas para el motor de declaraciones SAT.

Soporta:
- Fórmulas aritméticas simples: {3.1} + {3.2} * 0.12
- Expresiones CASE WHEN: CASE WHEN {5_SUM} > {3_SUM} THEN {5_SUM} - {3_SUM} ELSE 0 END
- Funciones matemáticas: max(), min(), abs()
"""

from .case_when_evaluator import CaseWhenEvaluator
from .formula_evaluator import FormulaEvaluator

__all__ = [
    "FormulaEvaluator",
    "CaseWhenEvaluator",
]
