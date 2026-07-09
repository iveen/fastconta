// frontend/src/services/publicRegistration.js
import axios from 'axios'

const publicApi = axios.create({
  baseURL: '/api/v1/public',
  headers: {
    'Content-Type': 'application/json'
  }
})

export const publicRegistrationApi = {
  /**
   * Registrar solicitud de nuevo tenant
   * @param {Object} payload - Datos de la solicitud
   * @returns {Promise<Object>} - Respuesta con ID de solicitud
   */
  register: async (payload) => {
    const response = await publicApi.post('/register', payload)
    return response.data
  }
}