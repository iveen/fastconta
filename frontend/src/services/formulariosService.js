import api from '@/services/api'

/**
 * @typedef {Object} FormularioSat
 * @property {string} id
 * @property {string} codigo
 * @property {string} version
 * @property {string} nombre
 * @property {string|null} descripcion
 * @property {string} fecha_vigencia_desde
 * @property {string|null} fecha_vigencia_hasta
 * @property {boolean} es_version_activa
 * @property {string|null} formulario_padre_id
 * @property {string|null} created_at
 * @property {string|null} updated_at
 * @property {number} [total_secciones]
 * @property {number} [total_casillas]
 */

export const formulariosService = {
  /**
   * Lista formularios con filtros y paginación
   * @param {Object} params
   * @param {string} [params.codigo]
   * @param {boolean} [params.es_version_activa]
   * @param {number} [params.skip]
   * @param {number} [params.limit]
   * @returns {Promise<{data: FormularioSat[], total: number}>}
   */
  async listar(params = {}) {
    const response = await api.get('/formularios-sat/', { params })
    return response.data
  },

  /**
   * Obtiene detalle completo de un formulario
   * @param {string} id
   * @returns {Promise<FormularioSat>}
   */
  async obtenerPorId(id) {
    const response = await api.get(`/formularios-sat/id/${id}`)
    return response.data
  },

  /**
   * Obtiene la versión vigente de un formulario
   * @param {string} codigo
   * @param {string} [fecha]
   * @returns {Promise<FormularioSat>}
   */
  async obtenerVigente(codigo, fecha) {
    const response = await api.get(`/formularios-sat/${codigo}/vigente`, {
      params: { fecha },
    })
    return response.data
  },

  /**
   * Obtiene historial de versiones
   * @param {string} codigo
   * @returns {Promise<{codigo: string, versiones: FormularioSat[], version_actual: FormularioSat|null, total_versiones: number}>}
   */
  async obtenerHistorial(codigo) {
    const response = await api.get(`/formularios-sat/${codigo}/historial`)
    return response.data
  },

  /**
   * Crea un nuevo formulario
   * @param {Object} data
   * @returns {Promise<FormularioSat>}
   */
  async crear(data) {
    const response = await api.post('/formularios-sat/', data)
    return response.data
  },

  /**
   * Actualiza un formulario existente
   * @param {string} id
   * @param {Object} data
   * @returns {Promise<FormularioSat>}
   */
  async actualizar(id, data) {
    const response = await api.patch(`/formularios-sat/${id}`, data)
    return response.data
  },

  /**
   * Duplica un formulario creando nueva versión
   * @param {string} id
   * @param {Object} data
   * @returns {Promise<FormularioSat>}
   */
  async duplicar(id, data) {
    const response = await api.post(`/formularios-sat/${id}/duplicar`, data)
    return response.data
  },

  /**
   * Elimina (soft delete) un formulario
   * @param {string} id
   * @returns {Promise<void>}
   */
  async eliminar(id) {
    await api.delete(`/formularios-sat/${id}`)
  },
}