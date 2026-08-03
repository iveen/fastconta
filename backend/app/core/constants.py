"""
Constantes compartidas para clasificación de facturas y motor tributario.

Este módulo centraliza valores que se usan en múltiples puntos del sistema,
evitando strings literales dispersos y facilitando el mantenimiento.

Single Point of Truth: Si SAT modifica las categorías, solo se cambia aquí.
"""
from enum import Enum


class ClasificacionGastoSAT(str, Enum):
    """
    Categorías oficiales de clasificación de gasto según SAT Guatemala.
    
    Se usa en:
    - FacturaElectronica.clasificacion_gasto_sat (tenant_models.py)
    - clasificar_gasto_sat() (contabilidad_service.py)
    - Endpoint de corrección manual (facturas.py)
    - Hoja electrónica (facturas.py)
    - Reglas de filtrado SAT-2237 (sat_2237.py)
    
    Ejemplo de uso:
        from app.core.constants import ClasificacionGastoSAT
        
        if ClasificacionGastoSAT.es_valido(nueva_clasificacion):
            factura.clasificacion_gasto_sat = nueva_clasificacion.upper()
        else:
            raise ValueError(f"Categoría inválida: {nueva_clasificacion}")
    """
    
    # Categorías estándar
    NORMAL = "NORMAL"
    COMBUSTIBLE = "COMBUSTIBLE"
    ACTIVO_FIJO = "ACTIVO_FIJO"
    MEDICAMENTO = "MEDICAMENTO"
    VEHICULO = "VEHICULO"
    PEQUENO_CONTRIBUYENTE = "PEQUENO_CONTRIBUYENTE"
    IMPORTACION = "IMPORTACION"
    
    # Categorías adicionales detectadas en hoja electrónica
    HOTEL_SERVICIOS = "HOTEL_SERVICIOS"
    TIMBRE_PRENSA = "TIMBRE_PRENSA"
    
    @classmethod
    def valores_validos(cls) -> list[str]:
        """Retorna lista de todos los valores válidos (strings)."""
        return [c.value for c in cls]
    
    @classmethod
    def es_valido(cls, valor: str) -> bool:
        """Verifica si un valor es una categoría válida (case-insensitive)."""
        if not valor:
            return False
        return valor.upper() in cls.valores_validos()
    
    @classmethod
    def obtener(cls, valor: str) -> "ClasificacionGastoSAT | None":
        """
        Obtiene el enum member desde un string (case-insensitive).
        Retorna None si no es válido.
        """
        if not valor:
            return None
        valor_upper = valor.upper()
        for member in cls:
            if member.value == valor_upper:
                return member
        return None


# ============================================================
# OTROS CATÁLOGOS (agregar aquí según se necesiten)
# ============================================================

class TipoOperacionFEL(str, Enum):
    """Tipos de operación en facturas electrónicas."""
    VENTA = "Venta"
    COMPRA = "Compra"
    
    @classmethod
    def valores_validos(cls) -> list[str]:
        return [c.value for c in cls]


class EstadoFacturaFEL(str, Enum):
    """Estados posibles de una factura electrónica."""
    ACTIVA = "Activa"
    ANULADA = "Anulada"
    
    @classmethod
    def valores_validos(cls) -> list[str]:
        return [c.value for c in cls]
