"""
Clase base abstracta para estrategias de cálculo de formularios SAT.

Cada formulario específico (SAT-2237, SAT-2027, SAT-1010, etc.) debe implementar
esta interfaz para integrarse con el motor genérico de declaraciones.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class FormularioCalculoStrategy(ABC):
    """
    Contrato para la lógica específica de cada formulario SAT.
    
    El motor genérico delega los cálculos particulares a la estrategia,
    manteniendo la lógica común (carga de estructura, evaluación de fórmulas,
    persistencia) en el servicio principal.
    """
    
    codigo_formulario: str  # Ej: "SAT-2237"
    
    @abstractmethod
    async def preparar_contexto(
        self, db: AsyncSession, empresa_id: int, anio: int, mes: int
    ) -> dict[str, Any]:
        """
        Carga datos adicionales que necesita este formulario específico.
        
        Ejemplos:
        - SAT-2237: carga remanente del período anterior
        - SAT-1010: carga acumulado del año para ISR progresivo
        
        Args:
            db: Sesión de base de datos
            empresa_id: ID de la empresa
            anio: Año del período
            mes: Mes del período
        
        Returns:
            Diccionario con datos contextuales específicos del formulario
        """
        pass
    
    @abstractmethod
    def calcular_totales_cabecera(
        self, valores: dict[str, Decimal], contexto: dict[str, Any]
    ) -> dict[str, int]:
        """
        Calcula los totales que van en la cabecera de DeclaracionImpuesto.
        
        Ejemplos:
        - SAT-2237: {debito, credito, impuesto_determinado, remanente_siguiente, ...}
        - SAT-1010: {isr_determinado, pago_a_cuenta, isr_a_pagar, ...}
        
        Args:
            valores: Diccionario {codigo_casilla: valor_calculado}
            contexto: Contexto preparado por preparar_contexto()
        
        Returns:
            Diccionario con los totales de la declaración
        """
        pass
    
    @abstractmethod
    def clasificar_valor_casilla(
        self, tipo_casilla: str, valor: Decimal
    ) -> tuple[Decimal, Decimal]:
        """
        Decide si un valor va en base_imponible o monto_impuesto.
        
        Cada formulario tiene su propia convención sobre qué valores
        se almacenan en cada campo del DetalleDeclaracionImpuesto.
        
        Args:
            tipo_casilla: Tipo de la casilla (BASE_IMPONIBLE, DEBITO_FISCAL, etc.)
            valor: Valor calculado para la casilla
        
        Returns:
            Tupla (base_imponible, monto_impuesto)
        """
        pass
    
    def aplicar_logica_post_calculo(
        self, db: AsyncSession, declaracion: Any, valores: dict[str, Decimal], contexto: dict[str, Any]
    ) -> None:
        """
        Hook opcional para lógica adicional después del cálculo principal.
        
        Ejemplo: SAT-2237 recalcula totales si hay ajustes manuales.
        
        Por defecto no hace nada. Las estrategias pueden sobrescribir este método.
        
        Args:
            db: Sesión de base de datos
            declaracion: Objeto DeclaracionImpuesto
            valores: Diccionario {codigo_casilla: valor_calculado}
            contexto: Contexto preparado por preparar_contexto()
        """
        pass

