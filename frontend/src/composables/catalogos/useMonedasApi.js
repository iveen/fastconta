import { ref } from 'vue'
import api from '@/services/api'

export function useMonedasApi() {
  const loading = ref(false)
  const error = ref(null)

  const listar = async (params = {}) => {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get('/monedas/', { params })
      return data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Error al cargar monedas'
      throw e
    } finally {
      loading.value = false
    }
  }

  const listarActivos = async () => {
    const { data } = await api.get('/monedas/activos')
    return data
  }

  const obtenerPorId = async (id) => {
    const { data } = await api.get(`/monedas/${id}`)
    return data
  }

  const crear = async (payload) => {
    const { data } = await api.post('/monedas/', payload)
    return data
  }

  const actualizar = async (id, payload) => {
    const { data } = await api.patch(`/monedas/${id}`, payload)
    return data
  }

  const eliminar = async (id) => {
    await api.delete(`/monedas/${id}`)
  }

  return {
    loading, error,
    listar, listarActivos, obtenerPorId, crear, actualizar, eliminar
  }
}