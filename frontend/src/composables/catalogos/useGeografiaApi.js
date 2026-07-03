import { ref } from 'vue'
import api from '@/services/api'

export function useGeografiaApi() {
  const loading = ref(false)
  const error = ref(null)

  // Departamentos
  const listarDepartamentos = async () => {
    const { data } = await api.get('/geografia/departamentos')
    return data
  }

  const crearDepartamento = async (payload) => {
    const { data } = await api.post('/geografia/departamentos', payload)
    return data
  }

  const actualizarDepartamento = async (id, payload) => {
    const { data } = await api.patch(`/geografia/departamentos/${id}`, payload)
    return data
  }

  const eliminarDepartamento = async (id) => {
    await api.delete(`/geografia/departamentos/${id}`)
  }

  // Municipios
  const listarMunicipios = async (departamentoId = null) => {
    loading.value = true
    try {
      const params = departamentoId ? { departamento_id: departamentoId } : {}
      const { data } = await api.get('/geografia/municipios', { params })
      return data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Error al cargar municipios'
      throw e
    } finally {
      loading.value = false
    }
  }

  const crearMunicipio = async (payload) => {
    const { data } = await api.post('/geografia/municipios', payload)
    return data
  }

  const actualizarMunicipio = async (id, payload) => {
    const { data } = await api.patch(`/geografia/municipios/${id}`, payload)
    return data
  }

  const eliminarMunicipio = async (id) => {
    await api.delete(`/geografia/municipios/${id}`)
  }

  return {
    loading,
    error,
    listarDepartamentos,
    crearDepartamento,
    actualizarDepartamento,
    eliminarDepartamento,
    listarMunicipios,
    crearMunicipio,
    actualizarMunicipio,
    eliminarMunicipio
  }
}