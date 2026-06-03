import api from '@/services/api'

export const activosFijosService = {
  // 1. Catalogos
  getCategorias: () => api.get('/api/v1/activos-fijos/categorias'),

  // 2. CRUD Activos
  getActivos: (empresaId) => api.get(`/api/v1/activos-fijos/?empresa_id=${empresaId}`),
  crearActivo: (empresaId, data) => api.post(`/api/v1/activos-fijos/?empresa_id=${empresaId}`, data),
  actualizarActivo: (empresaId, activoId, data) => api.put(`/api/v1/activos-fijos/${activoId}?empresa_id=${empresaId}`, data),
  
  // 3. Procesos y Reportes
  procesarDepreciacion: (empresaId, anio, mes) => api.post('/api/v1/activos-fijos/depreciacion-mensual', {
    empresa_id: empresaId,
    anio_periodo: anio,
    mes_periodo: mes
  }),
  getProyeccion: (activoId, empresaId) => api.get(`/api/v1/activos-fijos/${activoId}/proyeccion?empresa_id=${empresaId}`)
}