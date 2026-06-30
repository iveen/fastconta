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
      <button @click="logout" class="text-sm text-red-600 hover:text-red-800">
        Cerrar sesión
      </button>
    </div>
  </nav>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCompanyStore } from '@/stores/company'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const companyStore = useCompanyStore()
const authStore = useAuthStore()
const isOpen = ref(false)

const selectCompany = (companyId) => {
  companyStore.setCompany(companyId)
  isOpen.value = false
  // Opcional: recargar datos de la vista actual
  router.go(0)
}

const logout = () => {
  authStore.logout()
}

// Cerrar dropdown al hacer clic fuera
const handleClickOutside = (event) => {
  if (!event.target.closest('.relative')) {
    isOpen.value = false
  }
}

onMounted(() => {
  window.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  window.removeEventListener('click', handleClickOutside)
})
</script>