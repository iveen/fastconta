<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-600 via-blue-700 to-emerald-600 p-4">
    <div class="bg-white p-8 rounded-2xl shadow-2xl w-full max-w-md">
      <!-- Header -->
      <div class="text-center mb-8">
        <div class="relative w-16 h-16 bg-gradient-to-br from-blue-700 to-emerald-500 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
          <KeyRound class="w-8 h-8 text-white" />
        </div>
        <h1 class="text-2xl font-bold text-gray-900">Restituir Contraseña</h1>
        <p class="text-sm text-gray-600 mt-2">Ingresa tu correo para recibir un enlace de recuperación</p>
      </div>

      <!-- Mensaje de Éxito -->
      <div v-if="successMessage" class="bg-green-50 border-l-4 border-green-500 p-4 rounded-lg mb-6">
        <p class="text-sm text-green-800 font-medium">{{ successMessage }}</p>
        <router-link to="/login" class="block mt-3 text-sm text-blue-600 hover:underline font-semibold">
          ← Volver al inicio de sesión
        </router-link>
      </div>

      <!-- Formulario -->
      <form v-else @submit.prevent="handleRequest" class="space-y-6">
        <div>
          <label class="block text-gray-700 text-sm font-bold mb-2" for="email">
            Correo electrónico
          </label>
          <input
            v-model="email"
            type="email"
            id="email"
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
            placeholder="tu@empresa.com"
            required
          />
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full bg-gradient-to-r from-blue-700 to-emerald-600 text-white font-bold py-3 px-4 rounded-lg hover:from-blue-800 hover:to-emerald-700 transition-all shadow-md disabled:opacity-50"
        >
          {{ loading ? 'Enviando enlace...' : 'Enviar enlace de recuperación' }}
        </button>

        <router-link 
          to="/login" 
          class="block text-center text-sm text-gray-500 hover:text-gray-700 mt-4"
        >
          ← Volver al inicio de sesión
        </router-link>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '@/services/api'
import { KeyRound } from '@lucide/vue'

const email = ref('')
const loading = ref(false)
const successMessage = ref('')

async function handleRequest() {
  loading.value = true
  try {
    // El backend siempre retorna 200 por seguridad (respuesta ciega)
    const res = await api.post('/auth/request-password-reset', { email: email.value })
    successMessage.value = res.data.message || 'Si el correo existe en el sistema, recibirás un enlace válido por 5 minutos.'
  } catch (err) {
    // En caso de error de red o 500
    successMessage.value = 'Ocurrió un error al procesar la solicitud. Intenta nuevamente más tarde.'
  } finally {
    loading.value = false
  }
}
</script>