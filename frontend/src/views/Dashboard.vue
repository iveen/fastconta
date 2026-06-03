<!-- src/views/Dashboard.vue -->
<template>
  <div class="min-h-screen flex bg-gray-100">
    <!-- Sidebar -->
    <aside class="w-64 bg-gray-800 text-white flex flex-col">
      <div class="p-4 text-xl font-bold border-b border-gray-700">
        FastConta
      </div>
      <nav class="flex-1 p-4 space-y-2 overflow-y-auto">
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
        <router-link to="/dashboard/facturas" class="block py-2 px-3 rounded hover:bg-gray-700 transition">
          🧾 Facturas Electrónicas
        </router-link>
        <router-link to="/dashboard/sat-libros" class="block py-2 px-3 rounded hover:bg-gray-700 transition">
          📋 Libros IVA (SAT)
        </router-link>
        <router-link 
          v-if="authStore.canManageUsers" 
          to="/dashboard/usuarios" 
          class="block py-2 px-3 rounded hover:bg-gray-700 transition"
        >
          👥 Usuarios
        </router-link>
      </nav>

      <!-- 👇 PANEL DE PERFIL (parte inferior del sidebar) -->
      <div class="border-t border-gray-700 p-4 bg-gray-900/50">
        <div class="flex items-center gap-3">
          <!-- Avatar con iniciales -->
          <div class="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-sm flex-shrink-0 shadow-md">
            {{ authStore.initials }}
          </div>
          <!-- Info del usuario -->
          <div class="flex-1 min-w-0">
            <p class="text-sm font-semibold text-white truncate" :title="authStore.user?.full_name || authStore.user?.email">
              {{ authStore.user?.full_name || authStore.user?.email }}
            </p>
            <p class="text-xs text-blue-300 truncate" :title="authStore.roleLabel">
              {{ authStore.roleLabel }}
            </p>
            <p v-if="authStore.user?.tenant_name" class="text-[10px] text-gray-400 truncate mt-0.5" :title="authStore.user.tenant_name">
              🏢 {{ authStore.user.tenant_name }}
            </p>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main content -->
    <div class="flex-1 flex flex-col">
      <!-- Navbar -->
      <header class="bg-white shadow-md px-6 py-3 flex justify-between items-center">
        <h1 class="text-lg font-semibold text-gray-700">Dashboard</h1>

        <!-- 👇 Dropdown de usuario en el navbar -->
        <div class="relative" ref="dropdownRef">
          <button
            @click="showDropdown = !showDropdown"
            class="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-gray-100 transition"
          >
            <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-xs">
              {{ authStore.initials }}
            </div>
            <span class="text-sm text-gray-700 hidden sm:inline">{{ authStore.user?.full_name?.split(' ')[0] || 'Usuario' }}</span>
            <svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <!-- Dropdown menu -->
          <div
            v-if="showDropdown"
            class="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50"
          >
            <!-- Info del usuario en el dropdown -->
            <div class="px-4 py-3 border-b border-gray-100">
              <p class="text-sm font-semibold text-gray-900 truncate">{{ authStore.user?.full_name }}</p>
              <p class="text-xs text-gray-500 truncate">{{ authStore.user?.email }}</p>
              <div class="flex items-center gap-2 mt-2">
                <span class="px-2 py-0.5 text-xs font-medium rounded-full bg-blue-100 text-blue-700">
                  {{ authStore.roleLabel }}
                </span>
              </div>
            </div>

            <!-- Tenant info -->
            <div v-if="authStore.user?.tenant_name" class="px-4 py-2 border-b border-gray-100 text-xs text-gray-600">
              <span class="font-medium">Firma:</span> {{ authStore.user.tenant_name }}
            </div>

            <!-- Logout -->
            <button
              @click="handleLogout"
              class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition flex items-center gap-2"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              Cerrar sesión
            </button>
          </div>
        </div>
      </header>

      <!-- Page content -->
      <main class="flex-1 p-6">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const showDropdown = ref(false)
const dropdownRef = ref(null)

// Cerrar dropdown al hacer clic fuera
const handleClickOutside = (event) => {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
    showDropdown.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>