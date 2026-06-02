// src/services/users.js
import api from './api'

export const usersApi = {
  /**
   * Crear un nuevo usuario.
   * El backend validará si el rol es superadmin (requiere tenant_id) 
   * o tenant_manager (ignora tenant_id y usa el propio).
   */
  createUser: (payload) => api.post('/users/', payload),

  /**
   * Asignar una empresa a un usuario existente.
   */
  assignEmpresa: (userId, empresaId) => 
    api.post(`/users/${userId}/empresas`, { empresa_id: empresaId }),

  /**
   * Obtener empresas asignadas a un usuario (para futura expansión).
   */
  getUserEmpresas: (userId) => api.get(`/users/${userId}/empresas`)
}