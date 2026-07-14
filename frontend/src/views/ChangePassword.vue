<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-600 via-blue-700 to-emerald-600 p-4">
    <div class="bg-white p-8 rounded-2xl shadow-2xl w-full max-w-md">
      <!-- Header -->
      <div class="text-center mb-8">
        <div class="relative w-16 h-16 bg-gradient-to-br from-blue-700 to-emerald-500 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
          <KeyRound class="w-8 h-8 text-white" />
        </div>
        <h1 class="text-2xl font-bold text-gray-900">
          {{ authStore.mustChangePassword ? 'Configurar Nueva Contraseña' : 'Cambiar Contraseña' }}
        </h1>
        <p class="text-sm text-gray-600 mt-2">
          {{ authStore.mustChangePassword 
             ? 'Por seguridad, debes establecer una nueva contraseña antes de continuar.' 
             : 'Actualiza tu contraseña de acceso' }}
        </p>
      </div>

      <!-- Errores -->
      <div v-if="error" class="bg-red-50 border-l-4 border-red-500 p-4 rounded-lg mb-6">
        <p class="text-sm text-red-700 font-medium">{{ error }}</p>
        <ul v-if="Array.isArray(errorDetails)" class="list-disc list-inside text-xs text-red-600 mt-2 space-y-1">
          <li v-for="(err, i) in errorDetails" :key="i">{{ err }}</li>
        </ul>
      </div>

      <!-- Éxito -->
      <div v-if="success" class="bg-green-50 border-l-4 border-green-500 p-4 rounded-lg mb-6">
        <p class="text-sm text-green-700 font-medium">{{ success }}</p>
     0</div>

      <!-- Formulario -->
      <form v-if="!success" @submit.prevent="handleSubmit" class="space-y-5">
        
        <!-- ✅ CONDICIONAL: Solo mostrar si NO es el primer login forzado -->
        <div v-if="!authStore.mustChangePassword">
          <label class="block text-sm font-medium text-gray-700 mb-1">Contraseña Actual</label>
          <input
            v-model="form.current_password"
            type="password"
            required
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="••••••••"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Nueva Contraseña</label>
          <input
            v-model="form.new_password"
            type="password"
            required
            minlength="12"
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Mínimo 12 caracteres"
          />
          <p class="text-xs text-gray-500 mt-1">Debe tener mayúsculas, minúsculas, números y símbolos.</p>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Confirmar Nueva Contraseña</label>
          <input
            v-model="form.confirm_password"
            type="password"
            required
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
          {{ loading ? 'Procesando...' : (authStore.mustChangePassword ? 'Continuar al Sistema' : 'Actualizar Contraseña') }}
        </button>

        <!-- Botón para cancelar solo si es cambio voluntario -->
        <button
          v-if="!authStore.mustChangePassword"
          type="button"
          @click="router.back()"
          class="w-full text-center text-sm text-gray-600 hover:text-gray-800 mt-2"
        >
          Cancelar
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'
import { KeyRound } from '@lucide/vue'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const error = ref('')
const errorDetails = ref(null)
const success = ref('')

const form = reactive({
  current_password: '',
  new_password: '',
  confirm_password: ''
})

async function handleSubmit() {
  loading.value = true
  error.value = ''
  errorDetails.value = null

  try {
    if (authStore.mustChangePassword) {
      // ✅ FLUJO 1: Primer login forzado (sin current_password)
      await api.post('/auth/first-login-change-password', {
        new_password: form.new_password
      })
      
      // Limpiar el flag en el store
      authStore.mustChangePassword = false
      
      success.value = '✅ Contraseña configurada exitosamente. Redirigiendo...'
      setTimeout(() => {
        router.push('/dashboard')
      }, 1500)
      
    } else {
      // ✅ FLUJO 2: Cambio voluntario desde dentro de la app (con current_password)
      await api.post('/auth/change-password', {
        current_password: form.current_password,
        new_password: form.new_password
      })
      
      success.value = '✅ Contraseña actualizada exitosamente.'
      setTimeout(() => {
        router.push('/dashboard') // O a donde quieras redirigir
      }, 1500)
    }
  } catch (err) {
    const detail = err.response?.data?.detail
    if (typeof detail === 'object' && detail.errors) {
      error.value = 'La contraseña no cumple con los requisitos:'
      errorDetails.value = detail.errors
    } else {
      error.value = detail || 'Error al procesar la solicitud'
    }
  } finally {
    loading.value = false
  }
}
</script>