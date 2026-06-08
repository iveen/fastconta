import api from '@/services/api'

export const activosFijosService = {
  // 1. Catálogos (SIN el prefijo /api/v1 porque api ya lo tiene en baseURL)
  getCategorias: () => api.get('/activos-fijos/categorias'),
  
  // 2. CRUD Activos
  getActivos: (empresaId) => api.get(`/activos-fijos/?empresa_id=${empresaId}`),
  crearActivo: (empresaId, data) => api.post(`/activos-fijos/?empresa_id=${empresaId}`, data),
  actualizarActivo: (empresaId, activoId, data) => api.put(`/activos-fijos/${activoId}?empresa_id=${empresaId}`, data),
  
  // 3. Procesos y Reportes
  procesarDepreciacion: (empresaId, anio, mes) => api.post('/activos-fijos/depreciacion-mensual', {
    empresa_id: empresaId,
    anio_periodo: anio,
    mes_periodo: mes
  }),
  getProyeccion: (activoId, empresaId) => api.get(`/activos-fijos/${activoId}/proyeccion?empresa_id=${empresaId}`)
}