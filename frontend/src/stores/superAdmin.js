// frontend/src/stores/superAdmin.js
import { defineStore } from 'pinia'
import api from '@/services/api'

export const useSuperAdminStore = defineStore('superAdmin', {
  state: () => ({
    tenants: [],
    currentTenantId: null,
    currentTenant: null,
    currentEmpresaId: null,
    currentEmpresa: null,
    tenantRequests: [],
    pendingRequestsCount: 0,
    loading: false,
    error: null
  }),
  
  getters: {
    hasContext: (state) => !!state.currentTenantId,
    currentTenantName: (state) => state.currentTenant?.name || 'Sin tenant seleccionado',
    hasPendingRequests: (state) => state.pendingRequestsCount > 0
  },
  
  actions: {
    /**
     * Contar solicitudes pendientes (para badge en sidebar)
     */
    async countPendingRequests() {
      const token = localStorage.getItem('token')
      if (!token) {
        this.pendingRequestsCount = 0
        return 0
      }
      try {
        const response = await api.get('/tenant-requests/pending/count')
        this.pendingRequestsCount = response.data.pending_count
        return this.pendingRequestsCount
      } catch (err) {
        if (err.response?.status !== 401) {
          console.error('Error contando solicitudes:', err)
        }
        this.pendingRequestsCount = 0
        return 0
      }
    },

    async fetchTenants() {
      this.loading = true
      this.error = null
      try {
        const response = await api.get('/tenants/')
        this.tenants = response.data
        return this.tenants
      } catch (err) {
        console.error('Error cargando tenants:', err)
        this.error = err.response?.data?.detail || 'Error al cargar tenants'
        this.tenants = []
        throw err
      } finally {
        this.loading = false
      }
    },

    /**
     * Listar solicitudes con filtro opcional por estado
     */
    async fetchTenantRequests(statusFilter = null) {
      const token = localStorage.getItem('token')
      if (!token) {
        this.tenantRequests = []
        return []
      }
      this.loading = true
      this.error = null
      try {
        const params = statusFilter ? { status: statusFilter } : {}
        const response = await api.get('/tenant-requests/', { 
          params,
          timeout: 30000
        })
        this.tenantRequests = response.data
        return this.tenantRequests
      } catch (err) {
        console.error('Error cargando solicitudes:', err)
        if (err.response?.status !== 401) {
          this.error = err.response?.data?.detail || 'Error al cargar solicitudes'
        }
        this.tenantRequests = []
        throw err
      } finally {
        this.loading = false
      }
    },

    /**
     * Reenviar email de solicitud (permitiendo actualizar email)
     */
    async resendRequestEmail(requestId, newEmail = null) {
      this.loading = true
      this.error = null
      try {
        const payload = newEmail ? { contact_email: newEmail } : {}
        const response = await api.post(`/tenant-requests/${requestId}/resend-email`, payload)
        return response.data
      } catch (err) {
        console.error('Error reenviando email:', err)
        this.error = err.response?.data?.detail || 'Error al reenviar email'
        throw err
      } finally {
        this.loading = false
      }
    },
    /**
     * Reenviar credenciales de un tenant aprobado.
     * Genera nueva contraseña y envía email.
     */
    async resendTenantCredentials(requestId) {
      this.loading = true
      this.error = null
      try {
        const response = await api.post(`/tenant-requests/${requestId}/resend-credentials`)
        return response.data
      } catch (err) {
        console.error('Error reenviando credenciales:', err)
        this.error = err.response?.data?.detail || 'Error al reenviar credenciales'
        throw err
      } finally {
        this.loading = false
      }
    },

    /**
     * Aprobar solicitud (usa BackgroundTasks en backend, responde inmediatamente)
     */
    async approveTenantRequest(requestId, payload) {
      this.loading = true
      this.error = null
      try {
        console.log('🚀 Iniciando provisionamiento en background...')
        const response = await api.post(`/tenant-requests/${requestId}/approve`, payload)
        console.log('✅ Respuesta inmediata del backend:', response.data)
        
        // Recargar listas
        await this.countPendingRequests()
        await this.fetchTenantRequests()
        
        return response.data
      } catch (err) {
        console.error('❌ Error aprobando solicitud:', err)
        this.error = err.response?.data?.detail || 'Error al aprobar solicitud'
        throw err
      } finally {
        this.loading = false
      }
    },

    /**
     * Rechazar solicitud
     */
    async rejectTenantRequest(requestId, reason) {
      this.loading = true
      this.error = null
      try {
        const response = await api.post(`/tenant-requests/${requestId}/reject`, { reason })
        await this.countPendingRequests()
        await this.fetchTenantRequests()
        return response.data
      } catch (err) {
        console.error('Error rechazando solicitud:', err)
        this.error = err.response?.data?.detail || 'Error al rechazar solicitud'
        throw err
      } finally {
        this.loading = false
      }
    },

    /**
     * Desactivar tenant
     */
    async deactivateTenant(tenantPublicId, reason) {
      this.loading = true
      try {
        const response = await api.patch(
          `/tenants/${tenantPublicId}/deactivate`,
          null,
          { params: { reason } }
        )
        await this.fetchTenants()
        return response.data
      } catch (err) {
        console.error('Error desactivando tenant:', err)
        this.error = err.response?.data?.detail || 'Error al desactivar tenant'
        throw err
      } finally {
        this.loading = false
      }
    },

    /**
     * Reactivar tenant
     */
    async activateTenant(tenantPublicId) {
      this.loading = true
      try {
        const response = await api.patch(`/tenants/${tenantPublicId}/activate`)
        await this.fetchTenants()
        return response.data
      } catch (err) {
        console.error('Error reactivando tenant:', err)
        this.error = err.response?.data?.detail || 'Error al reactivar tenant'
        throw err
      } finally {
        this.loading = false
      }
    }
  }
})