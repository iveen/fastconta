import api from '@/services/api'

export const casillasService = {
  async listar(seccionId, params = {}) {
    const response = await api.get(`/casillas/?seccion_id=${seccionId}`, { params })
    return response.data
  },

  async obtenerPorId(id) {
    const response = await api.get(`/casillas/${id}`)
    return response.data
  },

  async crear(data) {
    const response = await api.post('/casillas/', data)
    return response.data
  },

  async actualizar(id, data) {
    const response = await api.patch(`/casillas/${id}`, data)
    return response.data
  },

  async eliminar(id) {
    await api.delete(`/casillas/${id}`)
  },
}