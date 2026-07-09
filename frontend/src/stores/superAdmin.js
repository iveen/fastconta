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
    // ... (acciones existentes de tenants)
    
    /**
     * Contar solicitudes pendientes (para badge en sidebar)
     * ✅ CORREGIDO: Verificar autenticación antes de hacer el request
     */
    async countPendingRequests() {
      // ✅ Verificar si hay un token antes de hacer el request
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
        // ✅ Solo loguear el error si NO es 401 (no autenticado)
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
     * ✅ CORREGIDO: Verificar autenticación antes de hacer el request
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
        console.log('📡 fetchTenantRequests: Haciendo request al backend...')
        const params = statusFilter ? { status: statusFilter } : {}
        
        const response = await api.get('/tenant-requests/', { 
          params,
          timeout: 30000  // 30 segundos de timeout
        })
        
        console.log('📡 fetchTenantRequests: Respuesta recibida:', response.data.length, 'solicitudes')
        this.tenantRequests = response.data
        return this.tenantRequests
        
      } catch (err) {
        console.error('❌ fetchTenantRequests: Error:', err)
        
        if (err.response?.status !== 401) {
          console.error('❌ fetchTenantRequests: Detalles:', err.response?.data)
          this.error = err.response?.data?.detail || 'Error al cargar solicitudes'
        }
        
        this.tenantRequests = []
        throw err
      } finally {
        this.loading = false
      }
    },
    
    /**
     * Aprobar solicitud y crear tenant + admin
     */
    async approveTenantRequest(requestId, payload) {
      this.loading = true
      this.error = null
      try {
        const response = await api.post(`/tenant-requests/${requestId}/approve`, payload)
        await this.countPendingRequests()
        await this.fetchTenantRequests()
        return response.data
      } catch (err) {
        console.error('Error aprobando solicitud:', err)
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
    },
    /**
     * Aprueba solicitud con tracking de progreso
     * @param {number} requestId 
     * @param {Object} payload 
     * @param {Function} onProgress - Callback para actualizar UI
     */
    async approveTenantRequestWithProgress(requestId, payload, onProgress) {
      this.loading = true
      this.error = null
      
      try {
        // Paso 1: Validando
        onProgress({
          step: 1,
          total: 4,
          message: 'Validando datos de la solicitud...',
          status: 'processing'
        })
        await new Promise(resolve => setTimeout(resolve, 500))
        
        // Paso 2: Creando schema
        onProgress({
          step: 2,
          total: 4,
          message: 'Creando estructura en la Base de Datos...',
          status: 'processing'
        })
        
        // Hacer el request real (puede tardar 10-60s)
        const response = await api.post(`/tenant-requests/${requestId}/approve`, payload, {
          timeout: 300000  // 5 minutos de timeout
        })
        
        console.log('✅ Respuesta del backend recibida:', response.data)
        
        // Paso 3: Completado
        onProgress({
          step: 3,
          total: 4,
          message: 'Creando usuario administrador...',
          status: 'processing'
        })
        await new Promise(resolve => setTimeout(resolve, 300))
        
        // Paso 4: Éxito
        onProgress({
          step: 4,
          total: 4,
          message: '¡Tenant creado exitosamente!',
          status: 'success'
        })
        
        // ✅ CORREGIDO: Manejar errores de actualización de contadores sin lanzar excepción
        try {
          await this.countPendingRequests()
        } catch (err) {
          console.warn('⚠️ Error actualizando contador de pendientes:', err)
          // No lanzar error, continuar
        }
        
        try {
          await this.fetchTenantRequests()
        } catch (err) {
          console.warn('⚠️ Error recargando lista de solicitudes:', err)
          // No lanzar error, continuar
        }
        
        console.log('✅ approveTenantRequestWithProgress completado exitosamente')
        return response.data
        
      } catch (err) {
        console.error('❌ Error en approveTenantRequestWithProgress:', err)
        this.error = err.response?.data?.detail || 'Error al aprobar solicitud'
        
        onProgress({
          step: 1,
          total: 4,
          message: `Error: ${this.error}`,
          status: 'error'
        })
        
        throw err
      } finally {
        this.loading = false
      }
    }
  }
})