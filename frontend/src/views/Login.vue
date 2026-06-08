<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-600 via-blue-700 to-emerald-600 p-4">
    <div class="bg-white p-8 rounded-2xl shadow-2xl w-full max-w-md">
      <!-- Logo y Branding -->
      <div class="text-center mb-8">
        <!-- Logo combinado: BookOpen + BarChart3 -->
        <div class="relative w-20 h-20 bg-gradient-to-br from-blue-700 to-emerald-500 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
          <BookOpen class="w-10 h-10 text-white" />
          <div class="absolute -bottom-1 -right-1 w-8 h-8 bg-emerald-400 rounded-lg flex items-center justify-center shadow-md border-2 border-white">
            <BarChart3 class="w-5 h-5 text-white" />
          </div>
        </div>
        <h1 class="text-3xl font-bold text-gray-900">FastConta</h1>
        <p class="text-sm text-gray-600 mt-1">Sistema Contable Profesional</p>
      </div>

      <!-- Formulario de Login -->
      <form @submit.prevent="handleLogin" class="space-y-6">
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

        <div>
          <label class="block text-gray-700 text-sm font-bold mb-2" for="password">
            Contraseña
          </label>
          <input
            v-model="password"
            type="password"
            id="password"
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
            placeholder="••••••••"
            required
          />
        </div>

        <button
          type="submit"
          class="w-full bg-gradient-to-r from-blue-700 to-emerald-600 text-white font-bold py-3 px-4 rounded-lg hover:from-blue-800 hover:to-emerald-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all shadow-md"
        >
          Iniciar sesión
        </button>
      </form>

      <!-- Error Message -->
      <p v-if="error" class="text-red-500 text-sm mt-4 text-center bg-red-50 p-3 rounded-lg">
        {{ error }}
      </p>

      <!-- Footer -->
      <div class="mt-6 text-center text-xs text-gray-400">
        <p>© 2026 FastConta - Todos los derechos reservados</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { BookOpen, BarChart3 } from '@lucide/vue'

const email = ref('')
const password = ref('')
const error = ref('')
const router = useRouter()
const authStore = useAuthStore()

async function handleLogin() {
  try {
    await authStore.login(email.value, password.value)
    router.push('/dashboard')
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al iniciar sesión'
  }
}
</script>