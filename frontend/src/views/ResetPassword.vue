<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-600 via-blue-700 to-emerald-600 p-4">
    <div class="bg-white p-8 rounded-2xl shadow-2xl w-full max-w-md">
      <!-- Header -->
      <div class="text-center mb-8">
        <div class="relative w-16 h-16 bg-gradient-to-br from-emerald-500 to-green-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
          <Lock class="w-8 h-8 text-white" />
        </div>
        <h1 class="text-2xl font-bold text-gray-900">Nueva Contraseña</h1>
        <p class="text-sm text-gray-600 mt-2">Define tu nueva contraseña de acceso</p>
      </div>

      <!-- Error (Token inválido/expirado) -->
      <div v-if="error" class="bg-red-50 border-l-4 border-red-500 p-4 rounded-lg mb-6">
        <p class="text-sm text-red-800 font-medium">{{ error }}</p>
        <router-link to="/forgot-password" class="block mt-3 text-sm text-blue-600 hover:underline font-semibold">
          Solicitar un nuevo enlace
        </router-link>
      </div>

      <!-- Formulario -->
      <form v-else @submit.prevent="handleReset" class="space-y-6">
        <div>
          <label class="block text-gray-700 text-sm font-bold mb-2">Nueva Contraseña</label>
          <input
            v-model="form.new_password"
            type="password"
            required
            minlength="12"
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
            placeholder="Mínimo 12 caracteres"
          />
          <p class="text-xs text-gray-500 mt-1">Debe tener mayúsculas, minúsculas, números y símbolos.</p>
        </div>

        <div>
          <label class="block text-gray-700 text-sm font-bold mb-2">Confirmar Contraseña</label>
          <input
            v-model="form.confirm_password"
            type="password"
            required
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
            placeholder="Repite la nueva contraseña"
          />
          <p v-if="form.new_password && form.new_password !== form.confirm_password" class="text-xs text-red-600 mt-1">
            Las contraseñas no coinciden
          </p>
        </div>

        <button
          type="submit"
          :disabled="loading || form.new_password !== form.confirm_password || form.new_password.length < 12"
          class="w-full bg-gradient-to-r from-blue-700 to-emerald-600 text-white font-bold py-3 px-4 rounded-lg hover:from-blue-800 hover:to-emerald-700 transition-all shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ loading ? 'Actualizando...' : 'Guardar Nueva Contraseña' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'
import { Lock } from '@lucide/vue'

const route = useRoute()
const router = useRouter()
const token = ref(route.query.token)
const loading = ref(false)
const error = ref('')

const form = reactive({
  new_password: '',
  confirm_password: ''
})

async function handleReset() {
  loading.value = true
  error.value = ''
  
  try {
    await api.post('/auth/confirm-password-reset', {
      token: token.value,
      new_password: form.new_password
    })
    
    // Redirigir al login con mensaje de éxito (usando query param)
    router.push({ path: '/login', query: { reset: 'success' } })
  } catch (err) {
    const detail = err.response?.data?.detail
    if (typeof detail === 'object' && detail.errors) {
      error.value = detail.errors.join('. ')
    } else {
      error.value = detail || 'El enlace es inválido o ha expirado (5 minutos).'
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (!token.value) {
    error.value = 'No se proporcionó un token de recuperación válido.'
  }
})
</script>