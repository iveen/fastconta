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
      'admin': 'Administrador',
      'tenant_manager': 'Gerente',
      'tenant_member': 'Miembro',
      'contador': 'Contador',
      'auxiliar': 'Auxiliar',
      'cliente': 'Cliente'
    }
    return roleMap[user.value.role] || user.value.role
  })

  // ✅ NUEVO: Verificar si puede gestionar usuarios
  const canManageUsers = computed(() => {
    if (!user.value?.role) return false
    return ['superadmin', 'admin', 'tenant_manager'].includes(user.value.role)
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
      
      // ✅ CORRECCIÓN: Construir objeto user desde los campos sueltos del backend
      user.value = {
        id: null,
        email: credentials.email || credentials.username,
        full_name: data.full_name,
        tenant_name: data.tenant_name,
        role: data.role
      }
      
      // 🎯 CRÍTICO: Cargar empresas del usuario después del login
      const companyStore = useCompanyStore()
      await companyStore.loadCompanies()
      
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
  const checkAuth = async () => {
    if (!token.value) return false
    
    try {
      const response = await api.get('/auth/me')
      
      // /auth/me probablemente retorna un objeto user completo
      if (response.data.user) {
        user.value = {
          id: response.data.id,
          email: response.data.email,
          full_name: response.data.full_name || response.data.name || response.data.email,
          tenant_name: response.data.tenant_name || response.data.tenant?.name || null,
          role: response.data.role || response.data.role_code || 'tenant_member'
        }
      } else {
        user.value = response.data
      }
      
      const companyStore = useCompanyStore()
      await companyStore.loadCompanies()
      
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
    isSuperAdmin,        // ✅ NUEVO
    initials,
    roleLabel,
    canManageUsers,
    login,
    logout,
    checkAuth
  }
})