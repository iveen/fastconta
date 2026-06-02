<!-- src/views/Empresas.vue -->
<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-6xl mx-auto space-y-6">
      <div class="flex justify-between items-center">
        <h1 class="text-2xl font-bold text-gray-800">Empresas</h1>
      </div>

      <!-- 🔹 SELECTOR DE TENANT (Solo Superadmin) -->
      <div v-if="authStore.isSuperAdmin" class="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <label class="block text-sm font-semibold text-blue-800 mb-1">🏢 Seleccionar Firma (Tenant)</label>
        <select 
          v-model="selectedTenantId" 
          @change="handleTenantChange" 
          class="w-full md:w-1/2 border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 p-2 border bg-white"
        >
          <option value="">-- Seleccione una firma para gestionar --</option>
          <option v-for="t in tenants" :key="t.id" :value="t.id">
            {{ t.name }} ({{ t.nit }})
          </option>
        </select>
      </div>

      <!-- Mensaje de error -->
      <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        {{ error }}
      </div>

      <!-- Mensaje de éxito -->
      <div v-if="successMsg" class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded flex justify-between items-center">
        <span>{{ successMsg }}</span>
        <button @click="successMsg = ''" class="text-sm underline hover:no-underline">Cerrar</button>
      </div>

      <!-- Estado vacío para superadmin sin tenant seleccionado -->
      <div v-if="authStore.isSuperAdmin && !selectedTenantId" class="bg-white rounded-lg shadow p-12 text-center border border-gray-200">
        <svg class="mx-auto h-16 w-16 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
        <p class="mt-4 text-gray-500 text-lg">Seleccione una firma en el filtro superior para visualizar sus empresas.</p>
      </div>

      <!-- Contenido principal (solo si hay tenant seleccionado o no es superadmin) -->
      <div v-else class="space-y-6">
        <!-- Botón Nueva Empresa (solo para non-superadmin) -->
        <div v-if="!authStore.isSuperAdmin" class="flex justify-end">
          <button
            @click="mostrarFormulario = !mostrarFormulario"
            class="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600 transition"
          >
            {{ mostrarFormulario ? 'Cancelar' : 'Nueva Empresa' }}
          </button>
        </div>

        <!-- Formulario de creación (solo para non-superadmin) -->
        <div v-if="mostrarFormulario && !authStore.isSuperAdmin" class="bg-white shadow-md rounded-lg p-6">
          <h3 class="text-lg font-semibold mb-4">Nueva Empresa</h3>
          <form @submit.prevent="crearEmpresa">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-gray-700 text-sm font-bold mb-2">Nombre</label>
                <input
                  v-model="nuevaEmpresa.nombre"
                  type="text"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label class="block text-gray-700 text-sm font-bold mb-2">NIT</label>
                <input
                  v-model="nuevaEmpresa.nit"
                  type="text"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div class="md:col-span-2">
                <label class="block text-gray-700 text-sm font-bold mb-2">Dirección</label>
                <input
                  v-model="nuevaEmpresa.direccion"
                  type="text"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <button
              type="submit"
              :disabled="cargando"
              class="mt-4 bg-green-500 text-white px-6 py-2 rounded-md hover:bg-green-600 transition disabled:opacity-50"
            >
              {{ cargando ? 'Creando...' : 'Crear Empresa' }}
            </button>
          </form>
        </div>

        <!-- Listado de empresas -->
        <div v-if="cargandoLista" class="text-center py-8 text-gray-500">
          Cargando empresas...
        </div>
        <div v-else-if="empresas.length === 0" class="bg-white shadow-md rounded-lg p-8 text-center text-gray-500">
          No hay empresas registradas.
        </div>
        <div v-else class="bg-white shadow-md rounded-lg overflow-hidden">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nombre</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">NIT</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Dirección</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="empresa in empresas" :key="empresa.id">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ empresa.nombre }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ empresa.nit }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ empresa.direccion || '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

const authStore = useAuthStore()

const empresas = ref([])
const tenants = ref([])
const selectedTenantId = ref('')
const mostrarFormulario = ref(false)
const cargando = ref(false)
const cargandoLista = ref(false)
const error = ref('')
const successMsg = ref('')

const nuevaEmpresa = ref({
  nombre: '',
  nit: '',
  direccion: ''
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
  // Si es superadmin, debe haber un tenant seleccionado
  if (authStore.isSuperAdmin && !selectedTenantId.value) {
    empresas.value = []
    return
  }

  cargandoLista.value = true
  error.value = ''
  try {
    const params = authStore.isSuperAdmin ? { tenant_id: selectedTenantId.value } : {}
    const response = await api.get('/empresas/', { params })
    empresas.value = response.data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al cargar empresas'
  } finally {
    cargandoLista.value = false
  }
}

const handleTenantChange = () => {
  empresas.value = []
  cargarEmpresas()
}

const crearEmpresa = async () => {
  cargando.value = true
  error.value = ''
  successMsg.value = ''
  try {
    await api.post('/empresas/', {
      nombre: nuevaEmpresa.value.nombre,
      nit: nuevaEmpresa.value.nit,
      direccion: nuevaEmpresa.value.direccion
    })
    successMsg.value = '✅ Empresa creada exitosamente.'
    nuevaEmpresa.value = { nombre: '', nit: '', direccion: '' }
    mostrarFormulario.value = false
    await cargarEmpresas()
  } catch (err) {
    const detail = err.response?.data?.detail
    if (err.response?.status === 403 && detail) {
      error.value = detail
    } else {
      error.value = detail || 'Error al crear empresa'
    }
  } finally {
    cargando.value = false
  }
}

onMounted(async () => {
  await fetchTenants()
  // Si es superadmin, preseleccionar el primer tenant
  if (authStore.isSuperAdmin && tenants.value.length > 0) {
    selectedTenantId.value = tenants.value[0].id
  }
  await cargarEmpresas()
})
</script>