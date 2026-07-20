<!-- src/components/Sidebar.vue -->
<template>
  <aside class="w-64 text-white flex flex-col shadow-xl" style="background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 100%);">
    <!-- Logo -->
    <div class="p-6 border-b border-blue-700">
      <div class="flex items-center gap-3">
        <div class="relative w-10 h-10 bg-linear-to-br from-emerald-400 to-emerald-500 rounded-lg flex items-center justify-center shadow-md shrink-0">
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
      <router-link to="/dashboard/empresas" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors group text-white" active-class="bg-blue-700">
        <Building2 class="w-5 h-5 text-blue-200 group-hover:text-white transition-colors" />
        Empresas
      </router-link>
      <router-link to="/dashboard/plan-cuentas" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors group text-white" active-class="bg-blue-700">
        <BookOpen class="w-5 h-5 text-blue-200 group-hover:text-white transition-colors" />
        Plan de Cuentas
      </router-link>
      <router-link to="/dashboard/partidas" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors group text-white" active-class="bg-blue-700">
        <FileText class="w-5 h-5 text-blue-200 group-hover:text-white transition-colors" />
        Partidas
      </router-link>
      <router-link to="/dashboard/reportes" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors group text-white" active-class="bg-blue-700">
        <BarChart3 class="w-5 h-5 text-blue-200 group-hover:text-white transition-colors" />
        Reportes
      </router-link>
      <router-link to="/dashboard/cierre" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors group text-white" active-class="bg-blue-700">
        <Lock class="w-5 h-5 text-blue-200 group-hover:text-white transition-colors" />
        Cierre Contable
      </router-link>
      <router-link to="/dashboard/periodos-fiscales" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors group text-white" active-class="bg-blue-700">
        <Calendar class="w-5 h-5 text-blue-200 group-hover:text-white transition-colors" />
        Períodos Fiscales
      </router-link>
      <router-link to="/dashboard/facturas" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors group text-white" active-class="bg-blue-700">
        <Receipt class="w-5 h-5 text-blue-200 group-hover:text-white transition-colors" />
        Facturas Electrónicas
      </router-link>
      <router-link to="/dashboard/sat-libros" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors group text-white" active-class="bg-blue-700">
        <BookOpen class="w-5 h-5 text-blue-200 group-hover:text-white transition-colors" />
        Libros IVA (SAT)
      </router-link>
      <router-link to="/declaraciones" class="flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors hover:bg-gray-800 text-gray-300 hover:text-white" active-class="bg-blue-600 text-white">
        <svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
        </svg>
        Declaraciones SAT
      </router-link>
      <router-link to="/dashboard/activos-fijos" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors group text-white" active-class="bg-blue-700">
        <CreditCard class="w-5 h-5 text-blue-200 group-hover:text-white transition-colors" />
        Activos Fijos
      </router-link>
      
      <!-- ✅ NUEVO: Módulo de Inventarios -->
      <router-link to="/dashboard/inventarios" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors group text-white" active-class="bg-blue-700">
        <Package class="w-5 h-5 text-blue-200 group-hover:text-white transition-colors" />
        Inventarios
      </router-link>
      
      <router-link to="/configuracion" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors group text-white" active-class="bg-blue-700">
        <Settings class="w-5 h-5 text-blue-200 group-hover:text-white transition-colors" />
        Configuración
      </router-link>
      <router-link v-if="authStore.canManageUsers" to="/dashboard/usuarios" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors group text-white" active-class="bg-blue-700">
        <Users class="w-5 h-5 text-blue-200 group-hover:text-white transition-colors" />
        Usuarios
      </router-link>
      <router-link v-if="authStore.isSuperAdmin" to="/superadmin" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors group text-white" active-class="bg-blue-700">
        <Shield class="w-5 h-5 text-blue-200 group-hover:text-white transition-colors" />
        Panel SuperAdmin
      </router-link>
    </nav>

    <!-- User Panel (Bottom) -->
    <div class="border-t border-blue-700 p-4 bg-blue-900/50">
      <!-- ... igual que antes ... -->
    </div>
  </aside>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth'
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
  Settings,
  Shield,
  Package,  // ✅ NUEVO: Icono para Inventarios
} from '@lucide/vue'

const authStore = useAuthStore()
</script>