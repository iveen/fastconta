<!-- src/views/Cierre.vue -->
<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-4xl mx-auto space-y-6">
      <h2 class="text-2xl font-bold text-gray-800">Cierre Contable</h2>
      
      <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">{{ error }}</div>
      <div v-if="exito" class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">{{ exito }}</div>

      <!-- 🔹 SELECTOR DE TENANT (Solo Superadmin) -->
      <div v-if="authStore.isSuperAdmin" class="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <label class="block text-sm font-semibold text-blue-800 mb-1">🏢 Seleccionar Firma (Tenant)</label>
        <select
          v-model="selectedTenantId"
          @change="handleTenantChange"
          class="w-full md:w-1/2 border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 p-2 border bg-white"
        >
          <option value="">-- Seleccione una firma --</option>
          <option v-for="t in tenants" :key="t.id" :value="t.id">
            {{ t.name }} ({{ t.nit }})
          </option>
        </select>
      </div>

      <!-- ✅ MENSAJE SI NO HAY EMPRESA SELECCIONADA -->
      <div v-if="!companyStore.selectedCompanyId" class="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-12 rounded-lg text-center">
        <svg class="w-12 h-12 mx-auto mb-3 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
        <p class="text-lg font-semibold">Selecciona una empresa desde la barra superior para ejecutar el cierre contable</p>
      </div>

      <!-- ✅ Panel de cierre (solo si hay empresa seleccionada) -->
      <div v-else class="bg-white shadow-md rounded-lg p-6">
        <!-- Info de empresa activa -->
        <div class="mb-4 pb-4 border-b border-gray-200 flex items-center gap-2">
          <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
          <span class="text-sm text-gray-600">Empresa activa:</span>
          <span class="font-semibold text-gray-800">{{ companyStore.currentCompany?.nombre || 'Desconocida' }}</span>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label class="block text-gray-700 text-sm font-bold mb-2">Período Fiscal</label>
            <select
              v-model="periodoId"
              :disabled="!companyStore.selectedCompanyId"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
            >
              <option value="">-- Seleccionar período --</option>
              <option v-for="per in periodosAbiertos" :key="per.id" :value="per.id">
                {{ per.nombre }} ({{ per.fecha_inicio }} - {{ per.fecha_fin }})
              </option>
            </select>
          </div>
        </div>

        <button
          @click="ejecutarCierre"
          :disabled="!periodoId || cargando"
          class="bg-orange-500 text-white px-6 py-2 rounded-md hover:bg-orange-600 transition disabled:opacity-50"
        >
          {{ cargando ? 'Cerrando...' : 'Ejecutar Cierre Anual' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useCompanyStore } from '@/stores/company'  // ✅ NUEVO

const authStore = useAuthStore()
const companyStore = useCompanyStore()  // ✅ NUEVO

const tenants = ref([])
const selectedTenantId = ref('')
const periodosAbiertos = ref([])
const periodoId = ref('')
const cargando = ref(false)
const error = ref('')
const exito = ref('')

const fetchTenants = async () => {
  if (!authStore.isSuperAdmin) return
  try {
    const res = await api.get('/tenants/')
    tenants.value = res.data.filter(t => !['sistema', 'system', 'public'].includes(t.schema_name))
  } catch (err) {
    console.error('Error cargando tenants:', err)
  }
}

const handleTenantChange = () => {
  periodosAbiertos.value = []
  periodoId.value = ''
  error.value = ''
  exito.value = ''
}

const cargarPeriodos = async () => {
  periodosAbiertos.value = []
  periodoId.value = ''
  
  if (!companyStore.selectedCompanyId) return
  
  try {
    const params = {}
    if (authStore.isSuperAdmin && selectedTenantId.value) {
      params.tenant_id = selectedTenantId.value
    }
    // ✅ El interceptor ya inyecta X-Company-Id automáticamente
    const resp = await api.get('/periodos-fiscales/', { params })
    periodosAbiertos.value = resp.data.filter(p => !p.cerrado)
  } catch {
    error.value = 'Error al cargar períodos'
  }
}

const ejecutarCierre = async () => {
  if (!companyStore.selectedCompanyId) {
    error.value = 'Debes seleccionar una empresa antes de ejecutar el cierre'
    return
  }
  
  cargando.value = true
  error.value = ''
  exito.value = ''
  
  try {
    const params = {
      periodo_id: periodoId.value
    }
    if (authStore.isSuperAdmin && selectedTenantId.value) {
      params.tenant_id = selectedTenantId.value
    }
    // ✅ No pasamos empresa_id, el interceptor lo inyecta automáticamente
    const resp = await api.post('/cierre/cierre-anual', null, { params })
    exito.value = resp.data.mensaje + '. Utilidad neta: ' + resp.data.utilidad_neta_periodo
    await cargarPeriodos()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al ejecutar el cierre'
  } finally {
    cargando.value = false
  }
}

// ✅ Watch: Recargar períodos cuando cambie la empresa seleccionada
watch(() => companyStore.selectedCompanyId, async (newId) => {
  if (newId) {
    await cargarPeriodos()
  } else {
    periodosAbiertos.value = []
    periodoId.value = ''
  }
})

onMounted(async () => {
  await fetchTenants()
  if (authStore.isSuperAdmin && tenants.value.length > 0) {
    selectedTenantId.value = tenants.value[0].id
  }
  // ✅ Cargar períodos si ya hay empresa seleccionada
  if (companyStore.selectedCompanyId) {
    await cargarPeriodos()
  }
})
</script>