"""
Registry de estrategias de cálculo para formularios SAT.

Permite registrar estrategias específicas para cada código de formulario
y obtenerlas dinámicamente en tiempo de ejecución.
"""

from typing import Type

from .base import FormularioCalculoStrategy

# Diccionario global que mapea código de formulario → clase de estrategia
_REGISTRY: dict[str, Type[FormularioCalculoStrategy]] = {}


def registrar(codigo: str):
    """
    Decorador para registrar una estrategia de cálculo.
    
    Uso:
        @registrar("SAT-2237")
        class SAT2237Strategy(FormularioCalculoStrategy):
            ...
    
    Args:
        codigo: Código del formulario (ej: "SAT-2237")
    """
    def decorator(cls: Type[FormularioCalculoStrategy]):
        _REGISTRY[codigo] = cls
        cls.codigo_formulario = codigo
        return cls
    return decorator


def obtener_estrategia(codigo: str) -> FormularioCalculoStrategy:
    """
    Obtiene una instancia de la estrategia para un formulario específico.
    
    Args:
        codigo: Código del formulario (ej: "SAT-2237")
    
    Returns:
        Instancia de la estrategia
    
    Raises:
        ValueError: Si no hay estrategia registrada para ese código
    """
    cls = _REGISTRY.get(codigo)
    if cls is None:
        raise ValueError(
            f"No hay estrategia registrada para el formulario '{codigo}'. "
            f"Formularios soportados: {list(_REGISTRY.keys())}"
        )
    return cls()


def formularios_soportados() -> list[str]:
    """
    Lista todos los códigos de formularios con estrategias registradas.
    
    Returns:
        Lista de códigos de formularios
    """
    return list(_REGISTRY.keys())
