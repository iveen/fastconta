<template>
  <div class="min-h-screen flex bg-gray-100">
    <!-- Sidebar -->
    <aside class="w-64 bg-gray-800 text-white flex flex-col">
      <div class="p-4 text-xl font-bold border-b border-gray-700">
        FastConta
      </div>
      <nav class="flex-1 p-4 space-y-2">
        <router-link to="/dashboard/empresas" class="block py-2 px-3 rounded hover:bg-gray-700 transition">
          🏢 Empresas
        </router-link>
        <router-link to="/dashboard/plan-cuentas" class="block py-2 px-3 rounded hover:bg-gray-700 transition">
          📋 Plan de Cuentas
        </router-link>
        <router-link to="/dashboard/partidas" class="block py-2 px-3 rounded hover:bg-gray-700 transition">
          📝 Partidas
        </router-link>
        <router-link to="/dashboard/reportes" class="block py-2 px-3 rounded hover:bg-gray-700 transition">
          📊 Reportes
        </router-link>
        <router-link to="/dashboard/cierre" class="block py-2 px-3 rounded hover:bg-gray-700 transition">
          🔒 Cierre Contable
        </router-link>
        <router-link to="/dashboard/periodos-fiscales" class="block py-2 px-3 rounded hover:bg-gray-700 transition">
            📅 Períodos Fiscales
        </router-link>
      </nav>
      <div class="p-4 border-t border-gray-700 text-sm text-gray-400">
        {{ authStore.user?.tenant_name }}
      </div>
    </aside>

    <!-- Main content -->
    <div class="flex-1 flex flex-col">
      <!-- Navbar -->
      <header class="bg-white shadow-md p-4 flex justify-between items-center">
        <h1 class="text-lg font-semibold text-gray-700">Dashboard</h1>
        <button @click="handleLogout" class="bg-red-500 text-white px-4 py-2 rounded-md hover:bg-red-600 transition">
          Cerrar sesión
        </button>
      </header>

      <!-- Page content -->
      <main class="flex-1 p-6">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>