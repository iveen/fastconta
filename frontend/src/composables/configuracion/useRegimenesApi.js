import { ref } from 'vue'
import api from '@/services/api'

export function useRegimenesApi() {
  const loading = ref(false)
  const error = ref(null)

  const listar = async (params = {}) => {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get('/regimenes-fiscales/', { params })
      return data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Error al cargar regímenes'
      throw e
    } finally {
      loading.value = false
    }
  }

  const listarActivos = async () => {
    const { data } = await api.get('/regimenes-fiscales/activos')
    return data
  }

  const obtenerPorId = async (id) => {
    const { data } = await api.get(`/regimenes-fiscales/${id}`)
    return data
  }

  const crear = async (payload) => {
    const { data } = await api.post('/regimenes-fiscales/', payload)
    return data
  }

  const actualizar = async (id, payload) => {
    const { data } = await api.patch(`/regimenes-fiscales/${id}`, payload)
    return data
  }

  const eliminar = async (id) => {
    await api.delete(`/regimenes-fiscales/${id}`)
  }

  return {
    loading, error,
    listar, listarActivos, obtenerPorId, crear, actualizar, eliminar
  }
}