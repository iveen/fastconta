// src/stores/auth.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue' // 👈 CRÍTICO: agregar 'computed' aquí
import api from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  // 👇 Propiedades computadas para los roles
  const isSuperAdmin = computed(() => user.value?.role === 'superadmin')
  const isTenantManager = computed(() => user.value?.role === 'tenant_manager')
  const canManageUsers = computed(() => isSuperAdmin.value || isTenantManager.value)

  const roleLabel = computed(() => {
    const map = {
      superadmin: 'Super Administrador',
      tenant_manager: 'Administrador de Firma',
      tenant_member: 'Miembro de Firma',
      tenant_client: 'Cliente (Solo Lectura)'
    }
    return map[user.value?.role] || user.value?.role || 'Invitado'
  })

  const initials = computed(() => {
    const name = user.value?.full_name || user.value?.email || '?'
    return name
      .split(' ')
      .map(n => n[0])
      .slice(0, 2)
      .join('')
      .toUpperCase()
  })

  async function login(email, password) {
    const response = await api.post('/auth/login', { email, password })
    token.value = response.data.access_token
    
    user.value = {
      email: email,
      full_name: response.data.full_name,
      role: response.data.role,
      tenant_name: response.data.tenant_name
    }
    localStorage.setItem('token', token.value)
    localStorage.setItem('user', JSON.stringify(user.value))
    return response.data
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  // 👈 Exportar las nuevas propiedades computadas
  return { 
    token, 
    user, 
    login, 
    logout,
    isSuperAdmin,
    isTenantManager,
    canManageUsers,
    roleLabel,
    initials
  }
})