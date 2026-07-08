// src/stores/superAdmin.js
import { defineStore } from 'pinia'
import api from '@/services/api'

export const useSuperAdminStore = defineStore('superAdmin', {
  state: () => ({
    tenants: [],
    currentTenantId: null,
    currentTenant: null,
    currentEmpresaId: null,
    currentEmpresa: null,
    loading: false,
    error: null
  }),
  
  getters: {
    // ✅ NUEVO: Verificar si hay contexto seleccionado
    hasContext: (state) => !!state.currentTenantId,
    
    // ✅ NUEVO: Obtener nombre del tenant actual
    currentTenantName: (state) => {
      return state.currentTenant?.name || 'Sin tenant seleccionado'
    }
  },
  
  actions: {
    // Cargar lista de tenants
    async fetchTenants() {
      this.loading = true
      this.error = null
      
      try {
        // ✅ CORREGIDO: Eliminar /api/v1/ duplicado (el proxy ya lo agrega)
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
    
    // Cargar empresas de un tenant específico
    async fetchTenantEmpresas(tenantId) {
      this.loading = true
      this.error = null
      
      try {
        // ✅ CORREGIDO: Ruta correcta sin /api/v1/ duplicado
        const response = await api.get(`/tenants/${tenantId}/empresas`)
        return response.data
      } catch (err) {
        console.error('Error cargando empresas del tenant:', err)
        this.error = err.response?.data?.detail || 'Error al cargar empresas'
        throw err
      } finally {
        this.loading = false
      }
    },
    
    // Establecer contexto completo (tenant + empresa)
    async setContext(tenantId, empresaId = null) {
      this.currentTenantId = tenantId
      this.currentEmpresaId = empresaId
      
      // Buscar tenant en la lista
      this.currentTenant = this.tenants.find(t => t.id === tenantId) || null
      
      // Si se especificó una empresa, cargar sus detalles
      if (empresaId) {
        try {
          const response = await api.get(`/tenants/${tenantId}/empresas/${empresaId}`)
          this.currentEmpresa = response.data.empresa
        } catch (err) {
          console.error('Error cargando detalles de empresa:', err)
          this.currentEmpresa = null
        }
      } else {
        this.currentEmpresa = null
      }
      
      // ✅ NUEVO: Persistir contexto en localStorage
      localStorage.setItem('superAdminContext', JSON.stringify({
        tenantId,
        empresaId
      }))
    },
    
    // Restaurar contexto desde localStorage
    async restoreContext() {
      const saved = localStorage.getItem('superAdminContext')
      if (!saved) return
      
      try {
        const { tenantId, empresaId } = JSON.parse(saved)
        
        // Verificar que el tenant aún existe
        await this.fetchTenants()
        const tenantExists = this.tenants.find(t => t.id === tenantId)
        
        if (tenantExists) {
          await this.setContext(tenantId, empresaId)
        } else {
          this.clearContext()
        }
      } catch (err) {
        console.error('Error restaurando contexto:', err)
        this.clearContext()
      }
    },
    
    // Limpiar contexto
    clearContext() {
      this.currentTenantId = null
      this.currentTenant = null
      this.currentEmpresaId = null
      this.currentEmpresa = null
      localStorage.removeItem('superAdminContext')
    }
  }
})