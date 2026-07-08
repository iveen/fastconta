// src/stores/auth.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'
import { useCompanyStore } from './company'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || null)
  const user = ref(null)
  const loading = ref(false)
  
  const isAuthenticated = computed(() => !!token.value)
  
  // ✅ NUEVO: Verificar si es SuperAdmin
  const isSuperAdmin = computed(() => {
    return user.value?.role === 'superadmin'
  })
  
  // ✅ NUEVO: Iniciales del usuario para el avatar
  const initials = computed(() => {
    if (!user.value) return 'U'
    const name = user.value.full_name || user.value.email || ''
    const parts = name.trim().split(' ')
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase()
    }
    return name.substring(0, 2).toUpperCase()
  })
  
  // ✅ NUEVO: Label del rol formateado
  const roleLabel = computed(() => {
    if (!user.value?.role) return 'Usuario'
    const roleMap = {
      'superadmin': 'Super Admin',
      'tenant_manager': 'Gerente',
      'tenant_member': 'Miembro',
      'tenant_client': 'Cliente'
    }
    return roleMap[user.value.role] || user.value.role
  })
  
  // ✅ NUEVO: Verificar si puede gestionar usuarios
  const canManageUsers = computed(() => {
    if (!user.value?.role) return false
    return ['superadmin', 'tenant_manager'].includes(user.value.role)
  })
  
  // ✅ NUEVO: Tenant ID del usuario (para flujo multi-tenant)
  const tenantId = computed(() => {
    return user.value?.tenant_id || null
  })
  
  // ✅ NUEVO: Schema del tenant (para queries dinámicas)
  const tenantSchema = computed(() => {
    return user.value?.schema || null
  })
  
  // Login
  const login = async (credentials) => {
    loading.value = true
    try {
      const response = await api.post('/auth/login', credentials)
      const data = response.data
      
      // Guardar token
      token.value = data.access_token
      localStorage.setItem('token', data.access_token)
      
      // ✅ CORREGIDO: Construir objeto user completo desde el backend
      user.value = {
        id: data.id || null,
        email: credentials.email || credentials.username,
        full_name: data.full_name,
        tenant_id: data.tenant_id,  // ✅ NUEVO: BIGINT interno
        tenant_public_id: data.tenant_public_id,  // ✅ NUEVO: UUID público
        tenant_name: data.tenant_name,
        schema: data.schema,  // ✅ NUEVO: Schema del tenant
        role: data.role
      }
      
      // ✅ CORREGIDO: Solo cargar empresas si NO es superadmin
      if (!isSuperAdmin.value) {
        const companyStore = useCompanyStore()
        await companyStore.loadCompanies()
      } else {
        console.log('👑 Superadmin detectado - omitiendo carga de empresas')
      }
      
      return data
    } catch (err) {
      console.error('Error en login:', err)
      throw err
    } finally {
      loading.value = false
    }
  }
  
  // Logout
  const logout = () => {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    
    const companyStore = useCompanyStore()
    companyStore.clearCompany()
    
    window.location.href = '/login'
  }
  
  // Verificar sesión al cargar la app
  // src/stores/auth.js
  const checkAuth = async () => {
    if (!token.value) return false
    
    try {
      const response = await api.get('/auth/me')
      
      if (response.data.user) {
        user.value = {
          id: response.data.id,
          email: response.data.email,
          full_name: response.data.full_name || response.data.name || response.data.email,
          tenant_name: response.data.tenant_name || response.data.tenant?.name || null,
          role: response.data.role || response.data.role_code || 'tenant_member',
          // ✅ AGREGAR: tenant_id y schema
          tenant_id: response.data.tenant_id,
          schema: response.data.schema
        }

        if (data.role !== 'superadmin') {
          const companyStore = useCompanyStore()
          await companyStore.loadCompanies()
        } else {
          console.log('👑 Superadmin detectado - omitiendo carga de empresas')
        }
      } else {
        user.value = response.data
      }
      
      // ✅ CORREGIDO: Solo cargar empresas si NO es superadmin
      const companyStore = useCompanyStore()
      if (user.value.role !== 'superadmin') {
        await companyStore.loadCompanies()
      } else {
        console.log('👑 Superadmin detectado - omitiendo carga de empresas')
        companyStore.availableCompanies = [] // Limpiar empresas para superadmin
      }
      
      return true
    } catch (err) {
      console.error('Error al verificar auth:', err)
      logout()
      return false
    }
  }

  return {
    token,
    user,
    loading,
    isAuthenticated,
    isSuperAdmin,
    initials,
    roleLabel,
    canManageUsers,
    tenantId,  // ✅ NUEVO
    tenantSchema,  // ✅ NUEVO
    login,
    logout,
    checkAuth
  }
})