"""
Strategy Pattern para motor de declaraciones SAT.

Cada formulario SAT tiene su propia estrategia que encapsula la lógica específica
de cálculo, mientras el motor genérico maneja la carga de estructura, evaluación
de fórmulas y persistencia.
"""

from .base import FormularioCalculoStrategy
from .registry import formularios_soportados, obtener_estrategia, registrar

__all__ = [
    "FormularioCalculoStrategy",
    "obtener_estrategia",
    "registrar",
    "formularios_soportados",
]
