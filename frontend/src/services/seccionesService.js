import api from '@/services/api'

export const seccionesService = {
  async listar(formularioId, params = {}) {
    const response = await api.get(`/secciones/?formulario_id=${formularioId}`, { params })
    return response.data
  },

  async obtenerPorId(id) {
    const response = await api.get(`/secciones/${id}`)
    return response.data
  },

  async crear(data) {
    const response = await api.post('/secciones/', data)
    return response.data
  },

  async actualizar(id, data) {
    const response = await api.patch(`/secciones/${id}`, data)
    return response.data
  },

  async eliminar(id) {
    await api.delete(`/secciones/${id}`)
  },
}