import { ref } from 'vue'
import api from '@/services/api'

export function useActividadesApi() {
  const loading = ref(false)
  const error = ref(null)

  const listar = async (params = {}) => {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get('/actividades-economicas/', { params })
      return data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Error al cargar actividades'
      throw e
    } finally {
      loading.value = false
    }
  }

  const listarActivas = async () => {
    const { data } = await api.get('/actividades-economicas/activas')
    return data
  }

  const obtenerPorId = async (id) => {
    const { data } = await api.get(`/actividades-economicas/${id}`)
    return data
  }

  const crear = async (payload) => {
    const { data } = await api.post('/actividades-economicas/', payload)
    return data
  }

  const actualizar = async (id, payload) => {
    const { data } = await api.patch(`/actividades-economicas/${id}`, payload)
    return data
  }

  const eliminar = async (id) => {
    await api.delete(`/actividades-economicas/${id}`)
  }

  return {
    loading, error,
    listar, listarActivas, obtenerPorId, crear, actualizar, eliminar
  }
}