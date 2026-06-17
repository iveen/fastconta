// src/services/declaraciones.js
import { useAuthStore } from '@/stores/auth'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

async function request(endpoint, options = {}) {
  // Importar useAuthStore DENTRO de la función para evitar problemas de carga
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

export const declaracionesApi = {
  generarSombra: (data) =>
    request('/declaraciones/sombra', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  obtener: (id) =>
    request(`/declaraciones/${id}`),

  aplicarAjuste: (id, casillaCodigo, data) =>
    request(`/declaraciones/${id}/casillas/${casillaCodigo}/ajuste`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  finalizar: (id) =>
    request(`/declaraciones/${id}/finalizar`, { method: 'POST' }),

  obtenerFacturas: (id, casillaCodigo) =>
    request(`/declaraciones/${id}/casillas/${casillaCodigo}/facturas`),
}