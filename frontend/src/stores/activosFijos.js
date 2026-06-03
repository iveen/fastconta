import { defineStore } from 'pinia'
import { ref } from 'vue'
import { activosFijosService } from '@/services/activosFijosService'

export const useActivosFijosStore = defineStore('activosFijos', () => {
  const activos = ref([])
  const categorias = ref([])
  const loading = ref(false)
  const error = ref(null)

  const fetchCategorias = async () => {
    try {
      const response = await activosFijosService.getCategorias()
      categorias.value = response.data
    } catch (err) {
      error.value = 'Error al cargar categorias de activos'
    }
  }

  const fetchActivos = async (empresaId) => {
    loading.value = true
    try {
      const response = await activosFijosService.getActivos(empresaId)
      activos.value = response.data
    } catch (err) {
      error.value = 'Error al cargar activos fijos'
    } finally {
      loading.value = false
    }
  }

  const procesarDepreciacionMensual = async (empresaId, anio, mes) => {
    loading.value = true
    try {
      const response = await activosFijosService.procesarDepreciacion(empresaId, anio, mes)
      return response.data // Retorna el resumen de la partida generada
    } catch (err) {
      error.value = err.response?.data?.detail || 'Error al procesar depreciacion'
      throw err
    } finally {
      loading.value = false
    }
  }

  return { 
    activos, 
    categorias, 
    loading, 
    error, 
    fetchCategorias, 
    fetchActivos,
    procesarDepreciacionMensual 
  }
})