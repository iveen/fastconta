# app/services/calculos/motor_calculo.py

from app.models.global_models import FormularioSat


class MotorCalculo:
    """
    Interpreta los metadatos de las casillas y calcula sus valores.
    Resuelve dependencias automáticamente (topological sort).
    """
    
    def calcular_formulario(
        self, 
        formulario: FormularioSat,
        contexto: dict  # Facturas, período, datos empresa, etc.
    ) -> dict[str, float]:
        """
        Returns: {codigo_casilla: valor_calculado}
        """
        # 1. Construir grafo de dependencias
        grafo = self._construir_grafo(formulario.secciones)
        
        # 2. Orden topológico (resuelve dependencias primero)
        orden = self._topological_sort(grafo)
        
        # 3. Calcular en orden
        valores = {}
        for codigo in orden:
            casilla = self._buscar_casilla(formulario, codigo)
            valores[codigo] = self._calcular_casilla(casilla, valores, contexto)
        
        return valores
    
    def _calcular_casilla(self, casilla, valores_previos, contexto):
        """Calcula una casilla según su tipo y metadatos"""
        
        # Caso 1: Casilla manual (usuario ingresa valor)
        if casilla.tipo_casilla == "MANUAL":
            return contexto.get("valores_manuales", {}).get(casilla.codigo, 0)
        
        # Caso 2: Suma de facturas filtradas
        if casilla.tipo_casilla == "SUMA_FACTURAS":
            facturas = self._filtrar_facturas(casilla, contexto)
            return sum(f[casilla.campo_origen_factura] for f in facturas)
        
        # Caso 3: Fórmula matemática
        if casilla.tipo_casilla == "CALCULADO":
            return self._evaluar_formula(
                casilla.formula_calculo, 
                valores_previos
            )
        
        # Caso 4: Función especializada (ISR progresivo, etc.)
        if casilla.funcion_calculo:
            funcion = FUNCIONES_REGISTRADAS[casilla.funcion_calculo]
            return funcion(
                valores_previos, 
                casilla.parametros_funcion
            )
        
        # Caso 5: Remanente de período anterior
        if casilla.tipo_casilla == "REMANENTE":
            return self._obtener_remanente(casilla, contexto)
        
        return 0
    
    def _evaluar_formula(self, formula: str, valores: dict) -> float:
        """
        Evalúa fórmulas como '3.1 - 3.2' o 'max(0, 3.4 - 3.5 - 3.6)'
        Reemplaza códigos por valores reales.
        """
        expresion = formula
        for codigo, valor in valores.items():
            expresion = expresion.replace(codigo, str(valor))
        
        # Sandbox seguro con funciones matemáticas básicas
        namespace = {
            "max": max, "min": min, "abs": abs,
            "round": round, "sum": sum,
        }
        return eval(expresion, {"__builtins__": {}}, namespace)


# Registro de funciones especializadas
FUNCIONES_REGISTRADAS = {
    "isr_progresivo": None, # calcular_isr_progresivo,
    "max_cero": lambda v, p: max(0, v.get(p["referencia"], 0)),
    "tasa_fija": lambda v, p: v.get(p["base"], 0) * p["tasa"],
}