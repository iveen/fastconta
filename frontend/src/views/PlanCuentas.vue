<template>
  <div>
    <h2 class="text-2xl font-bold mb-4">Plan de Cuentas</h2>

    <!-- Mensaje de error -->
    <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
      {{ error }}
    </div>

    <!-- Selector de empresa -->
    <div class="bg-white shadow-md rounded-lg p-4 mb-4">
      <label class="block text-gray-700 text-sm font-bold mb-2">Seleccionar Empresa</label>
      <select
        v-model="empresaSeleccionadaId"
        @change="cargarCuentas"
        class="w-full md:w-1/3 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="">-- Seleccione una empresa --</option>
        <option v-for="emp in empresas" :key="emp.id" :value="emp.id">
          {{ emp.nombre }}
        </option>
      </select>
    </div>

    <!-- Sin empresa seleccionada -->
    <div v-if="!empresaSeleccionadaId" class="bg-white shadow-md rounded-lg p-8 text-center text-gray-500">
      Seleccione una empresa para ver su plan de cuentas.
    </div>

    <!-- Listado de cuentas -->
    <div v-else>
      <div v-if="cargando" class="text-center py-8 text-gray-500">
        Cargando cuentas...
      </div>
      <div v-else-if="cuentas.length === 0" class="bg-white shadow-md rounded-lg p-8 text-center text-gray-500">
        No hay cuentas registradas para esta empresa. Ejecute el seed o cree una manualmente.
      </div>
      <div v-else class="bg-white shadow-md rounded-lg overflow-hidden">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Código</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nombre</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Naturaleza</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="cuenta in cuentas" :key="cuenta.id" class="hover:bg-gray-50">
              <td class="px-4 py-3 whitespace-nowrap text-sm font-mono text-gray-900">{{ cuenta.codigo }}</td>
              <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">{{ cuenta.nombre }}</td>
              <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500 capitalize">{{ cuenta.tipo }}</td>
              <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500 capitalize">{{ cuenta.naturaleza }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const empresas = ref([])
const empresaSeleccionadaId = ref('')
const cuentas = ref([])
const cargando = ref(false)
const error = ref('')

async function cargarEmpresas() {
  try {
    const response = await api.get('/empresas/')
    empresas.value = response.data
  } catch (err) {
    error.value = 'Error al cargar empresas'
  }
}

async function cargarCuentas() {
  if (!empresaSeleccionadaId.value) {
    cuentas.value = []
    return
  }
  cargando.value = true
  error.value = ''
  try {
    const response = await api.get('/plan-cuentas/', {
      params: { empresa_id: empresaSeleccionadaId.value }
    })
    cuentas.value = response.data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al cargar cuentas'
  } finally {
    cargando.value = false
  }
}

onMounted(() => {
  cargarEmpresas()
})
</script>