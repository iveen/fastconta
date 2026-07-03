import { ref } from 'vue'
import api from '@/services/api'

export function useTiposPersonaApi() {
  const loading = ref(false)
  const error = ref(null)

  const listar = async () => {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get('/tipos-persona/')
      return data.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Error al cargar tipos de persona'
      throw e
    } finally {
      loading.value = false
    }
  }

  const obtenerPorId = async (id) => {
    const { data } = await api.get(`/tipos-persona/${id}`)
    return data
  }

  const crear = async (payload) => {
    const { data } = await api.post('/tipos-persona/', payload)
    return data
  }

  const actualizar = async (id, payload) => {
    const { data } = await api.patch(`/tipos-persona/${id}`, payload)
    return data
  }

  const eliminar = async (id) => {
    await api.delete(`/tipos-persona/${id}`)
  }

  return {
    loading, error,
    listar, obtenerPorId, crear, actualizar, eliminar
  }
}