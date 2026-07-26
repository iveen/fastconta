import axios from 'axios'
import { useCompanyStore } from '@/stores/company'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json'
  },
  withCredentials: true
})

api.interceptors.request.use(config => {
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


// Interceptor para respuestas simplificado
api.interceptors.response.use(
  response => response,
  error => {
    // NO redirigir si el error viene del login (es parte del flujo normal)
    const isLoginRequest = error.config?.url?.includes('/auth/login')
    const isRefreshRequest = error.config?.url?.includes('/auth/refresh')
    
    if (
      error.response && 
      error.response.status === 401 && 
      !isLoginRequest && 
      !isRefreshRequest
    ) {
      // ❌ ELIMINAR: localStorage.removeItem('token')
      // La cookie se limpia automáticamente al expirar o vía /logout
      
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api