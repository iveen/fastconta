import axios from 'axios'
import { useCompanyStore } from '@/stores/company'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json'
  }
})

// Interceptor para añadir el token JWT
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  if (!(config.data instanceof FormData)) {
    config.headers['Content-Type'] = 'application/json'
  }

  // Inyectar contexto de empresa si existe
  const companyStore = useCompanyStore()
  if (companyStore.selectedCompanyId) {
    config.headers['X-Company-Id'] = companyStore.selectedCompanyId
  }
  return config
})

// Interceptor para manejar errores 401
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api