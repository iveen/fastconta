// src/services/publicApi.js
import axios from 'axios'

const publicApi = axios.create({
  baseURL: '/api/v1', // ✅ Debe ser igual que en api.js
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor opcional para depuración (no redirige al login)
publicApi.interceptors.response.use(
  response => response,
  error => {
    console.error('❌ Error en publicApi:', error.response?.status, error.response?.data)
    return Promise.reject(error)
  }
)

export default publicApi