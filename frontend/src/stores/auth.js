// src/stores/auth.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'
import { useCompanyStore } from './company'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || null)
  const user = ref(null)
  const loading = ref(false)
  
  // ✅ NUEVO: Estado de política de contraseñas
  const mustChangePassword = ref(false)
  const passwordExpiresAt = ref(null)
  const loginError = ref(null)  // Para mensajes detallados del login

  const requiresPasswordChange = computed(() => mustChangePassword.value)
  
  const isAuthenticated = computed(() => !!token.value)
  
  const isSuperAdmin = computed(() => {
    return user.value?.role === 'superadmin'
  })
  
  const initials = computed(() => {
    if (!user.value) return 'U'
    const name = user.value.full_name || user.value.email || ''
    const parts = name.trim().split(' ')
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase()
    }
    return name.substring(0, 2).toUpperCase()
  })
  
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
  
  const canManageUsers = computed(() => {
    if (!user.value?.role) return false
    return ['superadmin', 'tenant_manager'].includes(user.value.role)
  })
  
  const tenantId = computed(() => user.value?.tenant_id || null)
  const tenantSchema = computed(() => user.value?.schema || null)
  
  
  // ============================================================
  // LOGIN - Con manejo de errores complejos
  // ============================================================
  const login = async (credentials) => {
    loading.value = true
    loginError.value = null  // ✅ Limpiar error previo
    
    try {
      const response = await api.post('/auth/login', credentials)
      const data = response.data
      
      token.value = data.access_token
      localStorage.setItem('token', data.access_token)
      
      // ✅ Guardar estado de política de contraseñas
      mustChangePassword.value = data.must_change_password || false
      passwordExpiresAt.value = data.password_expires_at || null
      
      user.value = {
        id: data.user_id,
        public_id: data.public_id,
        email: credentials.email || credentials.username,
        full_name: data.full_name,
        tenant_id: data.tenant_id,
        tenant_public_id: data.tenant_public_id,
        tenant_name: data.tenant_name,
        schema: data.schema,
        role: data.role
      }
      
      if (!isSuperAdmin.value) {
        const companyStore = useCompanyStore()
        await companyStore.loadCompanies()
      } else {
        console.log('👑 Superadmin detectado - omitiendo carga de empresas')
      }
      
      return data
    } catch (err) {
      console.error('Error en login:', err)
      
      // ✅ NUEVO: Manejar errores complejos del backend
      const errorDetail = err.response?.data?.detail
      
      if (err.response?.status === 423) {
        // Cuenta bloqueada
        loginError.value = {
          type: 'locked',
          message: typeof errorDetail === 'object' 
            ? errorDetail.message 
            : 'Cuenta bloqueada',
          locked_until: typeof errorDetail === 'object' ? errorDetail.locked_until : null,
          remaining_minutes: typeof errorDetail === 'object' ? errorDetail.remaining_minutes : null,
          must_change_password: typeof errorDetail === 'object' ? errorDetail.must_change_password : false
        }
      } else if (err.response?.status === 401) {
        // Credenciales inválidas
        loginError.value = {
          type: 'invalid_credentials',
          message: typeof errorDetail === 'object' 
            ? errorDetail.message 
            : (errorDetail || 'Email o contraseña incorrectos'),
          remaining_attempts: typeof errorDetail === 'object' ? errorDetail.remaining_attempts : null,
          warning: typeof errorDetail === 'object' ? errorDetail.warning : null
        }
      } else {
        loginError.value = {
          type: 'generic',
          message: typeof errorDetail === 'string' 
            ? errorDetail 
            : 'Error al iniciar sesión'
        }
      }
      
      throw err
    } finally {
      loading.value = false
    }
  }

  // ============================================================
  // CAMBIO DE CONTRASEÑA
  // ============================================================

  const changePassword = async (payload) => {
    loading.value = true
    try {
      const response = await api.post('/auth/change-password', payload)
      mustChangePassword.value = false
      passwordExpiresAt.value = response.data.password_expires_at
      return response.data
    } catch (err) {
      console.error('Error cambiando contraseña:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  // ============================================================
  // LOGOUT
  // ============================================================
  const logout = () => {
    token.value = null
    user.value = null
    mustChangePassword.value = false
    passwordExpiresAt.value = null
    loginError.value = null
    localStorage.removeItem('token')
    const companyStore = useCompanyStore()
    companyStore.clearCompany()
    window.location.href = '/login'
  }

  // ============================================================
  // CHECK AUTH
  // ============================================================
  const checkAuth = async () => {
    if (!token.value) return false
    try {
      const response = await api.get('/auth/me')
      if (response.data.user) {
        user.value = {
          id: response.data.user_id,
          public_id: response.data.public_id,
          email: response.data.email,
          full_name: response.data.full_name || response.data.name || response.data.email,
          tenant_name: response.data.tenant_name || response.data.tenant?.name || null,
          role: response.data.role || response.data.role_code || 'tenant_member',
          tenant_id: response.data.tenant_id,
          schema: response.data.schema
        }
        
        // ✅ NUEVO: Verificar política de contraseñas desde /auth/me si el backend lo retorna
        mustChangePassword.value = response.data.must_change_password || false
        passwordExpiresAt.value = response.data.password_expires_at || null
        
        const companyStore = useCompanyStore()
        if (user.value.role !== 'superadmin') {
          await companyStore.loadCompanies()
        } else {
          console.log('👑 Superadmin detectado - omitiendo carga de empresas')
          companyStore.availableCompanies = []
        }
      }
      return true
    } catch (err) {
      console.error('Error al verificar auth:', err)
      logout()
      return false
    }
  }

  // ✅ NUEVO: Limpiar error de login (para reintentar)
  const clearLoginError = () => {
    loginError.value = null
  }

  return {
    token,
    user,
    loading,
    mustChangePassword,  // ✅ NUEVO
    passwordExpiresAt,   // ✅ NUEVO
    loginError,          // ✅ NUEVO
    requiresPasswordChange,  // ✅ NUEVO
    isAuthenticated,
    isSuperAdmin,
    initials,
    roleLabel,
    canManageUsers,
    tenantId,
    tenantSchema,
    login,
    changePassword,  // ✅ NUEVO
    logout,
    checkAuth,
    clearLoginError  // ✅ NUEVO
  }
})