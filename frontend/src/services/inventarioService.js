import api from '@/services/api' // Ajusta esta ruta a tu instancia de Axios

export const inventarioService = {
  // ============================================================
  // TOMAS DE INVENTARIO
  // ============================================================
  async listarTomas(filtros = {}) {
    const { data } = await api.get('/inventarios/tomas', { params: filtros })
    return data
  },

  async obtenerToma(publicId) {
    const { data } = await api.get(`/inventarios/tomas/${publicId}`)
    return data
  },

  async crearToma(payload) {
    const { data } = await api.post('/inventarios/tomas', payload)
    return data
  },

  async confirmarToma(publicId) {
    const { data } = await api.post(`/inventarios/tomas/${publicId}/confirmar`)
    return data
  },

  // ============================================================
  // ITEMS
  // ============================================================
  async listarItems(tomaPublicId) {
    const { data } = await api.get(`/inventarios/items/tomas/${tomaPublicId}`)
    return data
  },

  async eliminarItem(itemPublicId) {
    await api.delete(`/inventarios/items/${itemPublicId}`)
  },

  // ============================================================
  // IMPORTACIÓN ASÍNCRONA (JOBS)
  // ============================================================
  async importarArchivo(tomaPublicId, file, modo = 'REEMPLAZAR') {
    const formData = new FormData()
    formData.append('file', file)
    
    const { data } = await api.post(
      `/inventarios/importaciones/tomas/${tomaPublicId}/importar?modo=${modo}`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
    return data // Retorna el objeto Job con su public_id y estado inicial
  },

  async consultarEstadoJob(jobPublicId) {
    const { data } = await api.get(`/inventarios/importaciones/jobs/${jobPublicId}`)
    return data
  },

  async cancelarJob(jobPublicId) {
    const { data } = await api.post(`/inventarios/importaciones/jobs/${jobPublicId}/cancelar`)
    return data
  },

  // ============================================================
  // EXPORTACIÓN
  // ============================================================
  async exportarToma(tomaPublicId, formato = 'excel') {
    const response = await api.get(
      `/inventarios/export/tomas/${tomaPublicId}?formato=${formato}`,
      { responseType: 'blob' }
    )
    
    // Extraer nombre del archivo de los headers
    const disposition = response.headers['content-disposition']
    let filename = `inventario_${tomaPublicId}.${formato === 'excel' ? 'xlsx' : 'pdf'}`
    if (disposition && disposition.includes('filename=')) {
      const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition)
      if (matches != null && matches[1]) {
        filename = decodeURIComponent(matches[1].replace(/['"]/g, ''))
      }
    }
    
    return { blob: response.data, filename }
  },

  // ============================================================
  // COSTO DE VENTAS
  // ============================================================
  async calcularCostoVentas(tomaPublicId) {
    const { data } = await api.get(`/inventarios/costo-ventas/tomas/${tomaPublicId}`)
    return data
  }
}