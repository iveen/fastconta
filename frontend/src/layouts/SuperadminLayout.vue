<template>
  <div class="min-h-screen bg-gray-50 flex">
    <!-- Sidebar -->
    <aside class="w-64 bg-white border-r border-gray-200 flex flex-col">
      <!-- Header -->
      <div class="p-6 border-b border-gray-200">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-linear-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
            <span class="text-white font-bold text-lg">SA</span>
          </div>
          <div>
            <h1 class="text-lg font-bold text-gray-900">SuperAdmin</h1>
            <p class="text-xs text-gray-500">FastConta</p>
          </div>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 p-4 space-y-1">
        <RouterLink
          to="/superadmin/tenant-requests"
          class="flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="$route.path.includes('/tenant-requests')
            ? 'bg-blue-50 text-blue-700'
            : 'text-gray-700 hover:bg-gray-100'"
        >
          <span class="flex items-center gap-2">
            📥 Solicitudes
          </span>
          <span
            v-if="store.pendingRequestsCount > 0"
            class="bg-red-500 text-white text-xs px-2 py-0.5 rounded-full animate-pulse"
          >
            {{ store.pendingRequestsCount }}
          </span>
        </RouterLink>

        <RouterLink
          to="/superadmin/tenants"
          class="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="$route.path.includes('/tenants') && !$route.path.includes('requests')
            ? 'bg-blue-50 text-blue-700'
            : 'text-gray-700 hover:bg-gray-100'"
        >
          🏢 Tenants
        </RouterLink>

        <div class="pt-4 mt-4 border-t border-gray-200">
          <RouterLink
            to="/dashboard"
            class="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-gray-500 hover:bg-gray-100"
          >
            ← Volver al Dashboard
          </RouterLink>
        </div>
      </nav>

      <!-- User Info -->
      <div class="p-4 border-t border-gray-200">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-full bg-linear-to-r from-blue-600 to-purple-600 flex items-center justify-center text-white text-xs font-bold">
            {{ userInitials }}
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-gray-900 truncate">{{ userName }}</p>
            <p class="text-xs text-gray-500">Super Admin</p>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 p-6 overflow-auto">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { useSuperAdminStore } from '@/stores/superAdmin'
import { useAuthStore } from '@/stores/auth'

const $route = useRoute()
const store = useSuperAdminStore()
const authStore = useAuthStore()

const userName = computed(() => authStore.user?.full_name || 'Admin')
const userInitials = computed(() => {
  const name = authStore.user?.full_name || 'A'
  return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()
})

onMounted(async () => {
  // Cargar contador de pendientes al entrar al layout
  await store.countPendingRequests()
})
</script>