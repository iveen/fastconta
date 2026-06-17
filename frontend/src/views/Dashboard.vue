<!-- src/views/Dashboard.vue -->
<template>
  <div class="min-h-screen flex bg-gray-50">
    <!-- Sidebar -->
    <aside class="w-64 text-white flex flex-col shadow-xl" style="background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 100%);">
      <!-- Logo combinado -->
      <div class="p-6 border-b border-blue-700">
        <div class="flex items-center gap-3">
          <div class="relative w-10 h-10 bg-gradient-to-br from-emerald-400 to-emerald-500 rounded-lg flex items-center justify-center shadow-md flex-shrink-0">
            <BookOpen class="w-6 h-6 text-white" />
            <div class="absolute -bottom-1 -right-1 w-5 h-5 bg-blue-600 rounded flex items-center justify-center border-2 border-blue-900">
              <BarChart3 class="w-3 h-3 text-white" />
            </div>
          </div>
          <div>
            <h1 class="text-xl font-bold leading-tight text-white">FastConta</h1>
            <p class="text-xs text-blue-200">Sistema Contable</p>
          </div>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 p-4 space-y-1 overflow-y-auto">
        <router-link 
          to="/dashboard/empresas" 
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors group text-white"
          active-class="bg-blue-700"
        >
          <Building2 class="w-5 h-5 text-blue-200 group-hover:text-white transition-colors" />
          Empresas
        </router-link>

        <router-link 
          to="/dashboard/plan-cuentas" 
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors group text-white"
          active-class="bg-blue-700"
        >
          <BookOpen class="w-5 h-5 text-blue-200 group-hover:text-white transition-colors" />
          Plan de Cuentas
        </router-link>

        <router-link 
          to="/dashboard/partidas" 
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors group text-white"
          active-class="bg-blue-700"
        >
          <FileText class="w-5 h-5 text-blue-200 group-hover:text-white transition-colors" />
          Partidas
        </router-link>

        <router-link 
          to="/dashboard/reportes" 
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors group text-white"
          active-class="bg-blue-700"
        >
          <BarChart3 class="w-5 h-5 text-blue-200 group-hover:text-white transition-colors" />
          Reportes
        </router-link>

        <router-link 
          to="/dashboard/cierre" 
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors group text-white"
          active-class="bg-blue-700"
        >
          <Lock class="w-5 h-5 text-blue-200 group-hover:text-white transition-colors" />
          Cierre Contable
        </router-link>

        <router-link 
          to="/dashboard/periodos-fiscales" 
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors group text-white"
          active-class="bg-blue-700"
        >
          <Calendar class="w-5 h-5 text-blue-200 group-hover:text-white transition-colors" />
          Períodos Fiscales
        </router-link>

        <router-link 
          to="/dashboard/facturas" 
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors group text-white"
          active-class="bg-blue-700"
        >
          <Receipt class="w-5 h-5 text-blue-200 group-hover:text-white transition-colors" />
          Facturas Electrónicas
        </router-link>

        <router-link 
          to="/dashboard/sat-libros" 
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors group text-white"
          active-class="bg-blue-700"
        >
          <BookOpen class="w-5 h-5 text-blue-200 group-hover:text-white transition-colors" />
          Libros IVA (SAT)
        </router-link>

        <router-link 
          to="/declaraciones" 
          class="flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors hover:bg-gray-800 text-gray-300 hover:text-white"
          active-class="bg-blue-600 text-white"
        >
          <!-- Ícono Declaraciones (Documento con check) -->
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          </svg>
          Declaraciones SAT
        </router-link>

        <router-link 
          to="/dashboard/activos-fijos" 
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors group text-white"
          active-class="bg-blue-700"
        >
          <CreditCard class="w-5 h-5 text-blue-200 group-hover:text-white transition-colors" />
          Activos Fijos
        </router-link>

        <router-link
          v-if="authStore.canManageUsers"
          to="/dashboard/usuarios"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors group text-white"
          active-class="bg-blue-700"
        >
          <Users class="w-5 h-5 text-blue-200 group-hover:text-white transition-colors" />
          Usuarios
        </router-link>
      </nav>

      <!-- User Panel (Bottom) -->
      <div class="border-t border-blue-700 p-4 bg-blue-900/50">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-400 to-emerald-500 flex items-center justify-center text-white font-bold text-sm flex-shrink-0 shadow-md">
            {{ authStore.initials }}
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-semibold text-white truncate" :title="authStore.user?.full_name || authStore.user?.email">
              {{ authStore.user?.full_name || authStore.user?.email }}
            </p>
            <p class="text-xs text-blue-200 truncate" :title="authStore.roleLabel">
              {{ authStore.roleLabel }}
            </p>
            <p v-if="authStore.user?.tenant_name" class="text-[10px] text-blue-300 truncate mt-0.5" :title="authStore.user.tenant_name">
              🏢 {{ authStore.user.tenant_name }}
            </p>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col">
      <!-- Navbar -->
      <header class="bg-white shadow-md px-6 py-3 flex justify-between items-center">
        <h1 class="text-lg font-semibold text-gray-700">Dashboard</h1>
        
        <!-- User Dropdown -->
        <div class="relative" ref="dropdownRef">
          <button
            @click="showDropdown = !showDropdown"
            class="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-gray-100 transition"
          >
            <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-600 to-emerald-500 flex items-center justify-center text-white font-bold text-xs">
              {{ authStore.initials }}
            </div>
            <span class="text-sm text-gray-700 hidden sm:inline">
              {{ authStore.user?.full_name?.split(' ')[0] || 'Usuario' }}
            </span>
            <svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <!-- Dropdown Menu -->
          <div
            v-if="showDropdown"
            class="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50"
          >
            <!-- User Info -->
            <div class="px-4 py-3 border-b border-gray-100">
              <p class="text-sm font-semibold text-gray-900 truncate">{{ authStore.user?.full_name }}</p>
              <p class="text-xs text-gray-500 truncate">{{ authStore.user?.email }}</p>
              <div class="flex items-center gap-2 mt-2">
                <span class="px-2 py-0.5 text-xs font-medium rounded-full bg-blue-100 text-blue-700">
                  {{ authStore.roleLabel }}
                </span>
              </div>
            </div>

            <!-- Tenant Info -->
            <div v-if="authStore.user?.tenant_name" class="px-4 py-2 border-b border-gray-100 text-xs text-gray-600">
              <span class="font-medium">Firma:</span> {{ authStore.user.tenant_name }}
            </div>

            <!-- Logout -->
            <button
              @click="handleLogout"
              class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition flex items-center gap-2"
            >
              <LogOut class="w-4 h-4" />
              Cerrar sesión
            </button>
          </div>
        </div>
      </header>

      <!-- Page Content -->
      <main class="flex-1 p-6">
        <router-view />
      </main>
    </div>

    <ToastContainer />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import ToastContainer from './ToastContainer.vue'
import {
  BookOpen,
  BarChart3,
  Building2,
  FileText,
  Lock,
  Calendar,
  Receipt,
  CreditCard,
  Users,
  LogOut
} from '@lucide/vue'

const authStore = useAuthStore()
const router = useRouter()
const showDropdown = ref(false)
const dropdownRef = ref(null)

// Close dropdown when clicking outside
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