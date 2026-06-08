import api from '@/services/api'

export const planCuentasService = {
  // Obtener todas las cuentas del plan de una empresa
  getCuentas: (empresaId) => api.get(`/plan-cuentas/?empresa_id=${empresaId}`),
  
  // Obtener una cuenta específica
  getCuenta: (cuentaId) => api.get(`/plan-cuentas/${cuentaId}`),
  
  // Crear nueva cuenta
  crearCuenta: (data) => api.post('/plan-cuentas/', data),
  
  // Actualizar cuenta
  actualizarCuenta: (cuentaId, data) => api.put(`/plan-cuentas/${cuentaId}`, data),
  
  // Eliminar cuenta
  eliminarCuenta: (cuentaId) => api.delete(`/plan-cuentas/${cuentaId}`)
}