<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-600 via-blue-700 to-emerald-600 p-4">
    <div class="bg-white p-8 rounded-2xl shadow-2xl w-full max-w-md">
      <!-- Logo y Branding -->
      <div class="text-center mb-8">
        <div class="relative w-20 h-20 bg-gradient-to-br from-blue-700 to-emerald-500 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
          <BookOpen class="w-10 h-10 text-white" />
          <div class="absolute -bottom-1 -right-1 w-8 h-8 bg-emerald-400 rounded-lg flex items-center justify-center shadow-md border-2 border-white">
            <BarChart3 class="w-5 h-5 text-white" />
          </div>
        </div>
        <h1 class="text-3xl font-bold text-gray-900">FastConta</h1>
        <p class="text-sm text-gray-600 mt-1">Sistema Contable Profesional</p>
      </div>

      <!-- ✅ NUEVO: Errores visibles (ANTES del formulario) -->
      <!-- Error: Cuenta bloqueada -->
      <div v-if="authStore.loginError?.type === 'locked'" class="bg-red-50 border-l-4 border-red-500 p-4 rounded-lg mb-4">
        <div class="flex items-start gap-3">
          <Lock class="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div class="flex-1">
            <p class="font-semibold text-red-800 text-sm">Cuenta bloqueada</p>
            <p class="text-sm text-red-700 mt-1">{{ authStore.loginError.message }}</p>
            <p v-if="authStore.loginError.remaining_minutes" class="text-xs text-red-600 mt-2 font-medium">
              ️ Intenta nuevamente en {{ authStore.loginError.remaining_minutes }} minuto(s)
            </p>
            <p v-if="authStore.loginError.must_change_password" class="text-xs text-amber-700 mt-2">
              ⚠️ Deberás cambiar tu contraseña al desbloquearse
            </p>
          </div>
        </div>
      </div>

      <!-- Error: Credenciales inválidas -->
      <div v-else-if="authStore.loginError?.type === 'invalid_credentials'" class="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-lg mb-4">
        <div class="flex items-start gap-3">
          <AlertTriangle class="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div class="flex-1">
            <p class="font-semibold text-amber-800 text-sm">{{ authStore.loginError.message }}</p>
            <p v-if="authStore.loginError.remaining_attempts !== null && authStore.loginError.remaining_attempts !== undefined" 
               class="text-sm text-amber-700 mt-1">
              Intentos restantes: <strong>{{ authStore.loginError.remaining_attempts }}</strong>
            </p>
            <p v-if="authStore.loginError.warning" class="text-xs text-amber-600 mt-2 font-medium">
              ⚠️ {{ authStore.loginError.warning }}
            </p>
          </div>
        </div>
      </div>

      <!-- Error genérico -->
      <div v-else-if="authStore.loginError?.type === 'generic'" class="bg-red-50 border-l-4 border-red-500 p-4 rounded-lg mb-4">
        <p class="text-sm text-red-700">{{ authStore.loginError.message }}</p>
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
            @input="authStore.clearLoginError()"
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
            @input="authStore.clearLoginError()"
          />
        </div>
        <button
          type="submit"
          :disabled="authStore.loading"
          class="w-full bg-gradient-to-r from-blue-700 to-emerald-600 text-white font-bold py-3 px-4 rounded-lg hover:from-blue-800 hover:to-emerald-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ authStore.loading ? 'Iniciando sesión...' : 'Iniciar sesión' }}
        </button>

        <!-- ✅ NUEVO: Link para recuperar contraseña -->
        <div class="text-right">
          <router-link 
            to="/forgot-password" 
            class="text-sm text-blue-600 hover:text-blue-800 hover:underline transition-colors"
          >
            ¿Olvidaste tu contraseña?
          </router-link>
        </div>
      </form>

      <!-- Footer con link a registro -->
      <div class="mt-6 pt-6 border-t border-gray-200 text-center">
        <p class="text-sm text-gray-600">
          ¿Eres una firma contable y aún no tienes cuenta?
        </p>
        <router-link
          to="/registro"
          class="inline-block mt-2 text-blue-600 hover:text-blue-800 font-semibold transition-colors"
        >
          Solicita acceso aquí →
        </router-link>
      </div>

      <!-- Footer -->
      <div class="mt-6 text-center text-xs text-gray-400">
        <p>© 2026 FastConta - Todos los derechos reservados</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { BookOpen, BarChart3, Lock, AlertTriangle } from '@lucide/vue'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')

onMounted(() => {
  // ✅ Limpiar errores previos al montar el componente
  authStore.clearLoginError()
})

async function handleLogin() {
  authStore.clearLoginError()

  try {
    const data = await authStore.login({
      email: email.value,
      password: password.value
    })

    // ✅ Si debe cambiar contraseña, redirigir
    if (data.must_change_password) {
      console.log('⚠️ Usuario debe cambiar contraseña, redirigiendo...')
      router.push('/change-password')
      return
    }

    router.push('/dashboard')
  } catch (err) {
    // ✅ El error ya está capturado en authStore.loginError
    console.error('Error en login:', err)
  }
}
</script>