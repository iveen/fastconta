import api from '@/services/api'

export const felAPI = {
  getKPIs: async (params = {}) => {
    const response = await api.get('/facturas/kpis', { params })  // ✅ Sin /api/v1
    return response.data
  },
  uploadFacturas: async (files, empresaId) => {
    const formData = new FormData()
    files.forEach(file => formData.append('files', file))
    const response = await api.post(
      `/facturas/upload?empresa_id=${empresaId}`,  // ✅ Sin /api/v1
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
    return response.data
  },
  getJobs: async (params = {}) => {
    const response = await api.get('/facturas/jobs', { params })  // ✅ Sin /api/v1
    return response.data
  },
  getJobStatus: async (jobId) => {
    const response = await api.get(`/facturas/jobs/${jobId}`)  // ✅ Sin /api/v1
    return response.data
  },
  cancelJob: async (jobId) => {
    const response = await api.post(`/facturas/jobs/${jobId}/cancelar`)  // ✅ Sin /api/v1
    return response.data
  },
  reprocessJob: async (jobId, soloErrores = false) => {
    const response = await api.post(
      `/facturas/jobs/${jobId}/reprocesar?solo_errores=${soloErrores}`  // ✅ Sin /api/v1
    )
    return response.data
  },
}