<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold">Períodos Fiscales</h2>
      <button
        @click="mostrarForm = !mostrarForm"
        class="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600 transition"
      >
        {{ mostrarForm ? 'Cancelar' : 'Nuevo Período' }}
      </button>
    </div>

    <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
      {{ error }}
    </div>

    <!-- Formulario de creación -->
    <div v-if="mostrarForm" class="bg-white shadow-md rounded-lg p-6 mb-6">
      <h3 class="text-lg font-semibold mb-4">Nuevo Período Fiscal</h3>
      <form @submit.prevent="crearPeriodo">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label class="block text-gray-700 text-sm font-bold mb-2">Empresa</label>
            <select
              v-model="nuevoPeriodo.empresa_id"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              <option value="">-- Seleccionar --</option>
              <option v-for="emp in empresas" :key="emp.id" :value="emp.id">
                {{ emp.nombre }}
              </option>
            </select>
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
      No hay períodos registrados.
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
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const empresas = ref([])
const periodos = ref([])
const mostrarForm = ref(false)
const cargando = ref(false)
const cargandoLista = ref(false)
const error = ref('')

const nuevoPeriodo = ref({
  nombre: '',
  fecha_inicio: '',
  fecha_fin: '',
  empresa_id: ''
})

async function cargarEmpresas() {
  try {
    const resp = await api.get('/empresas/')
    empresas.value = resp.data
  } catch {
    error.value = 'Error al cargar empresas'
  }
}

async function cargarPeriodos() {
  cargandoLista.value = true
  try {
    const resp = await api.get('/periodos-fiscales/')
    periodos.value = resp.data
  } catch {
    error.value = 'Error al cargar períodos'
  } finally {
    cargandoLista.value = false
  }
}

async function crearPeriodo() {
  cargando.value = true
  error.value = ''
  try {
    await api.post('/periodos-fiscales/', nuevoPeriodo.value)
    nuevoPeriodo.value = { nombre: '', fecha_inicio: '', fecha_fin: '', empresa_id: '' }
    mostrarForm.value = false
    await cargarPeriodos()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al crear período'
  } finally {
    cargando.value = false
  }
}

onMounted(() => {
  cargarEmpresas()
  cargarPeriodos()
})
</script>