<!-- src/App.vue -->
<template>
  <div id="app">
    <div v-if="loading" class="min-h-screen flex items-center justify-center">
      <div class="text-center">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p class="text-gray-600">Cargando...</p>
      </div>
    </div>
    <router-view v-else />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const loading = ref(true)

onMounted(async () => {
  // ✅ CRÍTICO: Verificar sesión y cargar datos del usuario al iniciar
  const token = localStorage.getItem('token')
  if (token) {
    try {
      await authStore.checkAuth()
    } catch (err) {
      console.error('Error al verificar sesión:', err)
      // El logout ya se llama dentro de checkAuth si falla
    }
  }
  loading.value = false
})
</script>