<!-- src/components/TopNavbar.vue -->
<template>
<nav class="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
  <div class="flex items-center gap-4">
    <h1 class="text-xl font-bold text-blue-800">FastConta</h1>
    <!-- Dropdown de Empresas -->
    <div class="relative" v-if="companyStore.hasCompanies">
      <button
        @click="isOpen = !isOpen"
        class="flex items-center gap-2 bg-gray-50 hover:bg-gray-100 border border-gray-300 rounded-md px-3 py-1.5 text-sm font-medium text-gray-700 transition-colors"
      >
        <span>{{ companyStore.currentCompany?.nombre || 'Seleccionar Empresa' }}</span>
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
        </svg>
      </button>
      <h1> Hola Amigo!!!</h1>
      <div
        v-if="isOpen"
        class="absolute left-0 mt-2 w-64 bg-white border border-gray-200 rounded-md shadow-lg z-50 max-h-64 overflow-y-auto"
      >
        <ul class="py-1">
          <li
            v-for="company in companyStore.availableCompanies"
            :key="company.id"
            @click="selectCompany(company.id)"
            class="px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-700 cursor-pointer flex items-center gap-2"
            :class="{ 'bg-blue-50 text-blue-700 font-medium': company.id === companyStore.selectedCompanyId }"
          >
            <svg v-if="company.id === companyStore.selectedCompanyId" class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
            </svg>
            <span v-else class="w-4"></span>
            {{ company.nombre }}
            <span class="text-xs text-gray-500 ml-auto">{{ company.nit }}</span>
          </li>
        </ul>
      </div>
    </div>
  </div>

  <div class="flex items-center gap-4">
    <span class="text-sm text-gray-500 hidden md:block">{{ $route.name }}</span>
    
    <!-- Menú de Usuario -->
    <div class="relative">
      <button
        @click="isUserMenuOpen = !isUserMenuOpen"
        class="flex items-center gap-2 px-2 py-1 rounded-lg hover:bg-gray-100 transition-colors"
      >
        <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-600 to-emerald-500 text-white flex items-center justify-center font-bold text-sm shadow-sm">
          {{ authStore.initials }}
        </div>
        <div class="hidden md:block text-left">
          <p class="text-sm font-medium text-gray-700 leading-tight">{{ authStore.user?.full_name || authStore.user?.email }}</p>
          <p class="text-xs text-gray-500 leading-tight">{{ authStore.roleLabel }}</p>
        </div>
      </button>

      <!-- Dropdown Menu -->
      <div
        v-if="isUserMenuOpen"
        class="absolute right-0 mt-2 w-56 bg-white border border-gray-200 rounded-md shadow-lg z-50 py-1"
      >
        <!-- Información del usuario (mobile) -->
        <div class="px-4 py-2 border-b border-gray-100 md:hidden">
          <p class="text-sm font-medium text-gray-700">{{ authStore.user?.full_name }}</p>
          <p class="text-xs text-gray-500 truncate">{{ authStore.user?.email }}</p>
        </div>

        <!-- ✅ Opción Cambiar Contraseña - USANDO COMPONENTE LUCIDE -->
        <button
          @click="openChangePasswordModal"
          class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2 transition-colors"
        >
          <Key class="w-4 h-4 text-gray-500" />
          Cambiar Contraseña
        </button>

        <!-- Opción Cerrar Sesión - USANDO COMPONENTE LUCIDE -->
        <button
          @click="logout"
          class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2 border-t border-gray-100 transition-colors"
        >
          <LogOut class="w-4 h-4" />
          Cerrar Sesión
        </button>
      </div>
    </div>
  </div>

  <!-- ✅ MODAL: Cambiar Contraseña -->
  <div v-if="showChangePasswordModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
    <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-bold text-gray-900">Cambiar Contraseña</h3>
        <!-- ✅ BOTÓN CERRAR - USANDO COMPONENTE LUCIDE -->
        <button @click="showChangePasswordModal = false" class="text-gray-400 hover:text-gray-600">
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Errores -->
      <div v-if="pwdError" class="bg-red-50 border-l-4 border-red-500 p-3 rounded mb-4">
        <p class="text-sm text-red-700">{{ pwdError }}</p>
        <ul v-if="Array.isArray(pwdErrorDetail)" class="list-disc list-inside text-xs text-red-600 mt-1">
          <li v-for="(err, i) in pwdErrorDetail" :key="i">{{ err }}</li>
        </ul>
      </div>

      <!-- Éxito -->
      <div v-if="pwdSuccess" class="bg-green-50 border-l-4 border-green-500 p-3 rounded mb-4">
        <p class="text-sm text-green-700">{{ pwdSuccess }}</p>
      </div>

      <form @submit.prevent="handleChangePassword" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Contraseña Actual *</label>
          <input
            v-model="pwdForm.current_password"
            type="password"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Ingresa tu contraseña actual"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Nueva Contraseña *</label>
          <input
            v-model="pwdForm.new_password"
            type="password"
            required
            minlength="12"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Mínimo 12 caracteres"
          />
          <p class="text-xs text-gray-500 mt-1">Mínimo 12 caracteres, mayúsculas, números y símbolos.</p>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Confirmar Nueva Contraseña *</label>
          <input
            v-model="pwdForm.confirm_password"
            type="password"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Confirma tu nueva contraseña"
          />
          <p v-if="pwdForm.new_password && pwdForm.new_password !== pwdForm.confirm_password" class="text-xs text-red-600 mt-1">
            Las contraseñas no coinciden
          </p>
        </div>

        <div class="flex gap-2 pt-2">
          <button
            type="button"
            @click="showChangePasswordModal = false"
            class="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Cancelar
          </button>
          <button
            type="submit"
            :disabled="pwdLoading || pwdForm.new_password !== pwdForm.confirm_password || !pwdForm.new_password"
            class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {{ pwdLoading ? 'Cambiando...' : 'Actualizar' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</nav>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCompanyStore } from '@/stores/company'
import { useAuthStore } from '@/stores/auth'
// ✅ IMPORTAR COMPONENTES DE LUCIDE
import { Key, LogOut, X } from '@lucide/vue'

const router = useRouter()
const companyStore = useCompanyStore()
const authStore = useAuthStore()

const isOpen = ref(false)
const isUserMenuOpen = ref(false)

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

const selectCompany = (companyId) => {
  companyStore.setCompany(companyId)
  isOpen.value = false
  router.go(0)
}

const logout = () => {
  authStore.logout()
}

const openChangePasswordModal = () => {
  isUserMenuOpen.value = false
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
    
    // Cerrar modal después de 2 segundos
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

// Cerrar dropdowns al hacer clic fuera
const handleClickOutside = (event) => {
  if (!event.target.closest('.relative')) {
    isOpen.value = false
    isUserMenuOpen.value = false
  }
}

onMounted(() => {
  window.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  window.removeEventListener('click', handleClickOutside)
})
</script>
