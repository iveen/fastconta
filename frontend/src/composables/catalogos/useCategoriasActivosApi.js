import { ref } from 'vue'
import api from '@/services/api'

export function useCategoriasActivosApi() {
  const loading = ref(false)
  const error = ref(null)

  const listar = async (params = {}) => {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get('/categorias-activos/', { params })
      return data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Error al cargar categorías'
      throw e
    } finally {
      loading.value = false
    }
  }

  const listarActivos = async () => {
    const { data } = await api.get('/categorias-activos/activos')
    return data
  }

  const obtenerPorId = async (id) => {
    const { data } = await api.get(`/categorias-activos/${id}`)
    return data
  }

  const crear = async (payload) => {
    const { data } = await api.post('/categorias-activos/', payload)
    return data
  }

  const actualizar = async (id, payload) => {
    const { data } = await api.patch(`/categorias-activos/${id}`, payload)
    return data
  }

  const eliminar = async (id) => {
    await api.delete(`/categorias-activos/${id}`)
  }

  return {
    loading,
    error,
    listar,
    listarActivos,
    obtenerPorId,
    crear,
    actualizar,
    eliminar
  }
}