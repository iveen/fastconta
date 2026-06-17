import { ref, computed } from 'vue'
import { declaracionesApi } from '@/services/declaraciones'

// Estado global compartido (singleton)
const declaracionActual = ref(null)
const cargando = ref(false)
const error = ref('')

export function useDeclaraciones() {
  const generarSombra = async (empresaId, anio, mes, codigoFormulario = 'SAT-2237') => {
    cargando.value = true
    error.value = ''
    try {
      const res = await declaracionesApi.generarSombra({
        empresa_id: empresaId,
        anio,
        mes,
        codigo_formulario: codigoFormulario,
      })
      declaracionActual.value = await declaracionesApi.obtener(res.declaracion_id)
      return declaracionActual.value
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      cargando.value = false
    }
  }

  const recargar = async () => {
    if (declaracionActual.value) {
      cargando.value = true
      try {
        declaracionActual.value = await declaracionesApi.obtener(declaracionActual.value.id)
      } catch (e) {
        error.value = e.message
      } finally {
        cargando.value = false
      }
    }
  }

  const finalizar = async () => {
    if (!declaracionActual.value) return
    cargando.value = true
    try {
      await declaracionesApi.finalizar(declaracionActual.value.id)
      await recargar()
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      cargando.value = false
    }
  }

  const casillasPorSeccion = (seccion) => {
    if (!declaracionActual.value) return []
    return declaracionActual.value.detalles
      .filter(d => d.seccion === seccion)
      .sort((a, b) => a.casilla_codigo.localeCompare(b.casilla_codigo))
  }

  const totalPorSeccion = (seccion) => {
    const casillas = casillasPorSeccion(seccion)
    return {
      base: casillas.reduce((s, c) => s + Number(c.base_imponible || 0), 0),
      impuesto: casillas.reduce((s, c) => s + Number(c.monto_impuesto || 0), 0),
    }
  }

  return {
    declaracionActual,
    cargando,
    error,
    generarSombra,
    recargar,
    finalizar,
    casillasPorSeccion,
    totalPorSeccion,
  }
}