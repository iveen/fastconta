import { useAuthStore } from '@/stores/auth'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

async function request(endpoint, options = {}) {
  const auth = useAuthStore()
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${auth.token}`,
      ...options.headers,
    },
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }
  
  return response.json()
}

export const empresasApi = {
  listar: () => request('/empresas/'),
}