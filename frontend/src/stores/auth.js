import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  async function login(email, password) {
    const response = await api.post('/auth/login', { email, password })
    token.value = response.data.access_token
    user.value = {
      email: email,
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

  return { token, user, login, logout }
})