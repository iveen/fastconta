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

      <div class="bg-white shadow-md rounded-lg p-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label class="block text-gray-700 text-sm font-bold mb-2">Empresa</label>
            <select
              v-model="empresaId"
              @change="cargarPeriodos"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">-- Seleccionar empresa --</option>
              <option v-for="emp in empresas" :key="emp.id" :value="emp.id">
                {{ emp.nombre }}
              </option>
            </select>
          </div>
          <div>
            <label class="block text-gray-700 text-sm font-bold mb-2">Período Fiscal</label>
            <select
              v-model="periodoId"
              :disabled="!empresaId"
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
          :disabled="!empresaId || !periodoId || cargando"
          class="bg-orange-500 text-white px-6 py-2 rounded-md hover:bg-orange-600 transition disabled:opacity-50"
        >
          {{ cargando ? 'Cerrando...' : 'Ejecutar Cierre Anual' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const tenants = ref([])
const selectedTenantId = ref('')
const empresas = ref([])
const empresaId = ref('')
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

const cargarEmpresas = async () => {
  if (authStore.isSuperAdmin && !selectedTenantId.value) {
    empresas.value = []
    return
  }
  try {
    const params = authStore.isSuperAdmin ? { tenant_id: selectedTenantId.value } : {}
    const resp = await api.get('/empresas/', { params })
    empresas.value = resp.data
  } catch {
    error.value = 'Error al cargar empresas'
  }
}

const handleTenantChange = () => {
  empresaId.value = ''
  periodosAbiertos.value = []
  periodoId.value = ''
  cargarEmpresas()
}

const cargarPeriodos = async () => {
  periodosAbiertos.value = []
  periodoId.value = ''
  if (!empresaId.value) return
  try {
    const params = { empresa_id: empresaId.value }
    if (authStore.isSuperAdmin && selectedTenantId.value) {
      params.tenant_id = selectedTenantId.value
    }
    const resp = await api.get('/periodos-fiscales/', { params })
    periodosAbiertos.value = resp.data.filter(p => !p.cerrado)
  } catch {
    error.value = 'Error al cargar períodos'
  }
}

const ejecutarCierre = async () => {
  cargando.value = true
  error.value = ''
  exito.value = ''
  try {
    const params = {
      empresa_id: empresaId.value,
      periodo_id: periodoId.value
    }
    if (authStore.isSuperAdmin && selectedTenantId.value) {
      params.tenant_id = selectedTenantId.value
    }
    const resp = await api.post('/cierre/cierre-anual', null, { params })
    exito.value = resp.data.mensaje + '. Utilidad neta: ' + resp.data.utilidad_neta
    await cargarPeriodos()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al ejecutar el cierre'
  } finally {
    cargando.value = false
  }
}

onMounted(async () => {
  await fetchTenants()
  if (authStore.isSuperAdmin && tenants.value.length > 0) {
    selectedTenantId.value = tenants.value[0].id
  }
  await cargarEmpresas()
})
</script>