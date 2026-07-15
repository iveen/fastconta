<!-- src/components/TopNavbar.vue -->
<template>
  <header class="bg-white shadow-md px-6 py-3 flex justify-between items-center">
    <!-- Lado Izquierdo: Título + Selector de Empresa -->
    <div class="flex items-center gap-4">
      <h1 class="text-lg font-semibold text-gray-700">{{ pageTitle }}</h1>
      
      <div class="relative" ref="companyDropdownRef" v-if="companyStore.hasCompanies">
        <button @click="showCompanyDropdown = !showCompanyDropdown" class="flex items-center gap-2 bg-gray-50 hover:bg-gray-100 border border-gray-300 rounded-md px-3 py-1.5 text-sm font-medium text-gray-700 transition-colors min-w-50">
          <Building2 class="w-4 h-4 text-gray-500" />
          <span class="truncate">{{ companyStore.currentCompany?.nombre || 'Seleccionar Empresa' }}</span>
          <svg class="w-4 h-4 text-gray-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        
        <div v-if="showCompanyDropdown" class="absolute left-0 mt-2 w-72 bg-white border border-gray-200 rounded-md shadow-lg z-50 max-h-80 overflow-y-auto">
          <div class="px-4 py-2 border-b border-gray-100 bg-gray-50">
            <p class="text-xs font-semibold text-gray-600 uppercase">Cambiar de empresa</p>
          </div>
          <ul class="py-1">
            <li v-for="company in companyStore.availableCompanies" :key="company.id" @click="selectCompany(company.id)" class="px-4 py-2.5 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-700 cursor-pointer flex items-center gap-2" :class="{ 'bg-blue-50 text-blue-700 font-medium': company.id === companyStore.selectedCompanyId }">
              <svg v-if="company.id === companyStore.selectedCompanyId" class="w-4 h-4 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
              </svg>
              <span v-else class="w-4"></span>
              <div class="flex-1 min-w-0">
                <p class="truncate">{{ company.nombre }}</p>
                <p v-if="company.nit" class="text-xs text-gray-500">NIT: {{ company.nit }}</p>
              </div>
            </li>
          </ul>
        </div>
      </div>

      <div v-else-if="!companyStore.loading" class="text-sm text-amber-600 flex items-center gap-2">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <span>Sin empresas asignadas</span>
      </div>
    </div>

    <!-- Lado Derecho: User Dropdown -->
    <div class="relative" ref="userDropdownRef">
      <button @click="showUserDropdown = !showUserDropdown" class="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-gray-100 transition">
        <div class="w-8 h-8 rounded-full bg-linear-to-br from-blue-600 to-emerald-500 flex items-center justify-center text-white font-bold text-xs">
          {{ authStore.initials }}
        </div>
        <span class="text-sm text-gray-700 hidden sm:inline">
          {{ authStore.user?.full_name?.split(' ')[0] || 'Usuario' }}
        </span>
        <svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      <div v-if="showUserDropdown" class="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50">
        <div class="px-4 py-3 border-b border-gray-100">
          <p class="text-sm font-semibold text-gray-900 truncate">{{ authStore.user?.full_name }}</p>
          <p class="text-xs text-gray-500 truncate">{{ authStore.user?.email }}</p>
          <div class="flex items-center gap-2 mt-2">
            <span class="px-2 py-0.5 text-xs font-medium rounded-full bg-blue-100 text-blue-700">
              {{ authStore.roleLabel }}
            </span>
          </div>
        </div>
        <div v-if="authStore.user?.tenant_name" class="px-4 py-2 border-b border-gray-100 text-xs text-gray-600">
          <span class="font-medium">Firma:</span> {{ authStore.user.tenant_name }}
        </div>

        <!-- Opción Cambiar Contraseña -->
        <button @click="openChangePasswordModal" class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition flex items-center gap-2">
          <Key class="w-4 h-4 text-gray-500" />
          Cambiar Contraseña
        </button>

        <!-- Opción Cerrar Sesión -->
        <button @click="handleLogout" class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition flex items-center gap-2">
          <LogOut class="w-4 h-4" />
          Cerrar sesión
        </button>
      </div>
    </div>
  </header>

  <!-- MODAL: Cambiar Contraseña -->
  <div v-if="showChangePasswordModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
    <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-bold text-gray-900">Cambiar Contraseña</h3>
        <button @click="showChangePasswordModal = false" class="text-gray-400 hover:text-gray-600">
          <X class="w-5 h-5" />
        </button>
      </div>

      <div v-if="pwdError" class="bg-red-50 border-l-4 border-red-500 p-3 rounded mb-4">
        <p class="text-sm text-red-700">{{ pwdError }}</p>
        <ul v-if="Array.isArray(pwdErrorDetail)" class="list-disc list-inside text-xs text-red-600 mt-1">
          <li v-for="(err, i) in pwdErrorDetail" :key="i">{{ err }}</li>
        </ul>
      </div>

      <div v-if="pwdSuccess" class="bg-green-50 border-l-4 border-green-500 p-3 rounded mb-4">
        <p class="text-sm text-green-700">{{ pwdSuccess }}</p>
      </div>

      <form @submit.prevent="handleChangePassword" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Contraseña Actual *</label>
          <input v-model="pwdForm.current_password" type="password" required class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="Ingresa tu contraseña actual" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Nueva Contraseña *</label>
          <input v-model="pwdForm.new_password" type="password" required minlength="12" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="Mínimo 12 caracteres" />
          <p class="text-xs text-gray-500 mt-1">Mínimo 12 caracteres, mayúsculas, números y símbolos.</p>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Confirmar Nueva Contraseña *</label>
          <input v-model="pwdForm.confirm_password" type="password" required class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="Confirma tu nueva contraseña" />
          <p v-if="pwdForm.new_password && pwdForm.new_password !== pwdForm.confirm_password" class="text-xs text-red-600 mt-1">Las contraseñas no coinciden</p>
        </div>
        <div class="flex gap-2 pt-2">
          <button type="button" @click="showChangePasswordModal = false" class="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors">Cancelar</button>
          <button type="submit" :disabled="pwdLoading || pwdForm.new_password !== pwdForm.confirm_password || !pwdForm.new_password" class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
            {{ pwdLoading ? 'Cambiando...' : 'Actualizar' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useCompanyStore } from '@/stores/company'
import { Building2, Key, LogOut, X } from '@lucide/vue'

const authStore = useAuthStore()
const companyStore = useCompanyStore()
const router = useRouter()
const route = useRoute()

const showCompanyDropdown = ref(false)
const showUserDropdown = ref(false)
const companyDropdownRef = ref(null)
const userDropdownRef = ref(null)

// Estado del Modal de Contraseña
const showChangePasswordModal = ref(false)
const pwdLoading = ref(false)
const pwdError = ref('')
const pwdErrorDetail = ref(null)
const pwdSuccess = ref('')
const pwdForm = reactive({
  current_password: '',
  new_password: '',
  confirm_password: ''
})

const pageTitle = computed(() => {
  const titles = {
    'Empresas': 'Empresas',
    'PlanCuentas': 'Plan de Cuentas',
    'Partidas': 'Partidas de Diario',
    'PartidaDetalle': 'Detalle de Partida',
    'Reportes': 'Reportes Financieros',
    'Cierre': 'Cierre Contable',
    'PeriodosFiscales': 'Períodos Fiscales',
    'Facturas': 'Facturas Electrónicas',
    'FacturaDetalle': 'Detalle de Factura',
    'SATLibros': 'Libros IVA (SAT)',
    'Declaraciones': 'Declaraciones SAT',
    'ActivosFijos': 'Activos Fijos',
    'ActivosFijosCrear': 'Nuevo Activo Fijo',
    'ActivosFijosEditar': 'Editar Activo Fijo',
    'ActivosFijosProyeccion': 'Proyección de Activo',
    'LibroMayor': 'Libro Mayor',
    'ConfiguracionHub': 'Configuración del Sistema',
    'ConfiguracionFormulariosSAT': 'Formularios SAT',
    'Usuarios': 'Gestión de Usuarios',
    'SuperAdmin': 'Gestión SuperAdmin',
  }
  return titles[route.name] || 'Dashboard'
})

const selectCompany = (companyId) => {
  companyStore.setCompany(companyId)
  showCompanyDropdown.value = false
  router.go(0)
}

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

const openChangePasswordModal = () => {
  showUserDropdown.value = false
  showChangePasswordModal.value = true
  pwdError.value = ''
  pwdSuccess.value = ''
  pwdForm.current_password = ''
  pwdForm.new_password = ''
  pwdForm.confirm_password = ''
}

async function handleChangePassword() {
  pwdLoading.value = true
  pwdError.value = ''
  pwdSuccess.value = ''
  pwdErrorDetail.value = null

  try {
    await authStore.changePassword({
      current_password: pwdForm.current_password,
      new_password: pwdForm.new_password
    })
    
    pwdSuccess.value = '✅ Contraseña actualizada correctamente. Se ha enviado un correo de confirmación.'
    pwdForm.current_password = ''
    pwdForm.new_password = ''
    pwdForm.confirm_password = ''
    
    setTimeout(() => {
      showChangePasswordModal.value = false
    }, 2000)
  } catch (err) {
    console.error('Error cambiando contraseña:', err)
    const detail = err.response?.data?.detail
    
    if (typeof detail === 'object' && detail.errors) {
      pwdError.value = 'La contraseña no cumple con los requisitos:'
      pwdErrorDetail.value = detail.errors
    } else {
      pwdError.value = detail || 'Error al cambiar la contraseña'
    }
  } finally {
    pwdLoading.value = false
  }
}

const handleClickOutside = (event) => {
  if (companyDropdownRef.value && !companyDropdownRef.value.contains(event.target)) {
    showCompanyDropdown.value = false
  }
  if (userDropdownRef.value && !userDropdownRef.value.contains(event.target)) {
    showUserDropdown.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>