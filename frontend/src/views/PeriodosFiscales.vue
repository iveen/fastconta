<!-- src/views/PeriodosFiscales.vue -->
<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-6xl mx-auto space-y-6">
      <div class="flex justify-between items-center">
        <h2 class="text-2xl font-bold text-gray-800">Períodos Fiscales</h2>
        <button
          @click="mostrarForm = !mostrarForm"
          class="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600 transition"
          :disabled="!empresaFiltroId"
        >
          {{ mostrarForm ? 'Cancelar' : 'Nuevo Período' }}
        </button>
      </div>

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

      <!-- Filtro por empresa -->
      <div class="bg-white shadow-md rounded-lg p-4">
        <label class="block text-gray-700 text-sm font-bold mb-2">Filtrar por Empresa</label>
        <select
          v-model="empresaFiltroId"
          @change="cargarPeriodos"
          class="w-full md:w-1/3 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Todas las empresas</option>
          <option v-for="emp in empresas" :key="emp.id" :value="emp.id">{{ emp.nombre }}</option>
        </select>
      </div>

      <!-- Formulario de creación -->
      <div v-if="mostrarForm && empresaFiltroId" class="bg-white shadow-md rounded-lg p-6">
        <h3 class="text-lg font-semibold mb-4">Nuevo Período Fiscal</h3>
        <form @submit.prevent="crearPeriodo">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label class="block text-gray-700 text-sm font-bold mb-2">Empresa</label>
              <input :value="empresaFiltroNombre" disabled class="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-100 text-gray-700" />
            </div>
            <div>
              <label class="block text-gray-700 text-sm font-bold mb-2">Nombre</label>
              <input
                v-model="nuevoPeriodo.nombre"
                type="text"
                placeholder="Ej: 2026"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label class="block text-gray-700 text-sm font-bold mb-2">Fecha Inicio</label>
              <input
                v-model="nuevoPeriodo.fecha_inicio"
                type="date"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label class="block text-gray-700 text-sm font-bold mb-2">Fecha Fin</label>
              <input
                v-model="nuevoPeriodo.fecha_fin"
                type="date"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
          </div>
          <button
            type="submit"
            :disabled="cargando"
            class="bg-green-500 text-white px-6 py-2 rounded-md hover:bg-green-600 transition disabled:opacity-50"
          >
            {{ cargando ? 'Creando...' : 'Crear Período' }}
          </button>
        </form>
      </div>

      <!-- Listado de períodos -->
      <div v-if="cargandoLista" class="text-center py-8 text-gray-500">Cargando...</div>
      <div v-else-if="periodos.length === 0" class="bg-white shadow-md rounded-lg p-8 text-center text-gray-500">
        No hay períodos fiscales registrados{{ empresaFiltroId ? ' para la empresa seleccionada' : '' }}.
      </div>
      <div v-else class="bg-white shadow-md rounded-lg overflow-hidden">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nombre</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fecha Inicio</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fecha Fin</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="per in periodos" :key="per.id" class="hover:bg-gray-50">
              <td class="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">{{ per.nombre }}</td>
              <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">{{ per.fecha_inicio }}</td>
              <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">{{ per.fecha_fin }}</td>
              <td class="px-4 py-3 whitespace-nowrap text-sm">
                <span :class="per.cerrado ? 'text-red-600' : 'text-green-600'">
                  {{ per.cerrado ? 'Cerrado' : 'Abierto' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const tenants = ref([])
const selectedTenantId = ref('')
const empresas = ref([])
const empresaFiltroId = ref('')
const periodos = ref([])
const mostrarForm = ref(false)
const cargando = ref(false)
const cargandoLista = ref(false)
const error = ref('')
const exito = ref('')

const nuevoPeriodo = ref({
  nombre: '',
  fecha_inicio: '',
  fecha_fin: '',
  empresa_id: ''
})

const empresaFiltroNombre = computed(() => {
  const emp = empresas.value.find(e => e.id === empresaFiltroId.value)
  return emp ? emp.nombre : ''
})

// 🔹 Cargar lista de tenants solo si es superadmin
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
  empresaFiltroId.value = ''
  periodos.value = []
  cargarEmpresas()
}

const cargarPeriodos = async () => {
  cargandoLista.value = true
  try {
    const params = {}
    if (empresaFiltroId.value) params.empresa_id = empresaFiltroId.value
    if (authStore.isSuperAdmin && selectedTenantId.value) {
      params.tenant_id = selectedTenantId.value
    }
    const resp = await api.get('/periodos-fiscales/', { params })
    periodos.value = resp.data
  } catch {
    error.value = 'Error al cargar períodos'
  } finally {
    cargandoLista.value = false
  }
}

const crearPeriodo = async () => {
  if (!empresaFiltroId.value) {
    error.value = 'Debe seleccionar una empresa antes de crear un período.'
    return
  }
  cargando.value = true
  error.value = ''
  exito.value = ''
  try {
    await api.post('/periodos-fiscales/', {
      nombre: nuevoPeriodo.value.nombre,
      fecha_inicio: nuevoPeriodo.value.fecha_inicio,
      fecha_fin: nuevoPeriodo.value.fecha_fin,
      empresa_id: empresaFiltroId.value
    })
    exito.value = 'Período creado correctamente.'
    nuevoPeriodo.value = { nombre: '', fecha_inicio: '', fecha_fin: '' }
    mostrarForm.value = false
    await cargarPeriodos()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al crear período'
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
  await cargarPeriodos()
})
</script>