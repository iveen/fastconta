<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold">Empresas</h2>
      <button
        @click="mostrarFormulario = !mostrarFormulario"
        class="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600 transition"
      >
        {{ mostrarFormulario ? 'Cancelar' : 'Nueva Empresa' }}
      </button>
    </div>

    <!-- Mensaje de error -->
    <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
      {{ error }}
    </div>

    <!-- Formulario de creación -->
    <div v-if="mostrarFormulario" class="bg-white shadow-md rounded-lg p-6 mb-6">
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
      No hay empresas registradas. Crea la primera usando el botón "Nueva Empresa".
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
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const empresas = ref([])
const mostrarFormulario = ref(false)
const cargando = ref(false)
const cargandoLista = ref(false)
const error = ref('')

const nuevaEmpresa = ref({
  nombre: '',
  nit: '',
  direccion: ''
})

async function cargarEmpresas() {
  cargandoLista.value = true
  error.value = ''
  try {
    const response = await api.get('/empresas/')
    empresas.value = response.data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al cargar empresas'
  } finally {
    cargandoLista.value = false
  }
}

async function crearEmpresa() {
  cargando.value = true
  error.value = ''
  try {
    await api.post('/empresas/', {
      nombre: nuevaEmpresa.value.nombre,
      nit: nuevaEmpresa.value.nit,
      direccion: nuevaEmpresa.value.direccion
    })
    // Limpiar formulario y recargar lista
    nuevaEmpresa.value = { nombre: '', nit: '', direccion: '' }
    mostrarFormulario.value = false
    await cargarEmpresas()
  } catch (err) {
    const detail = err.response?.data?.detail
    if (err.response?.status === 403 && detail) {
      error.value = detail  // Ej: "Límite de empresas alcanzado (5) en plan freemium."
    } else {
      error.value = detail || 'Error al crear empresa'
    }
  } finally {
    cargando.value = false
  }
}

onMounted(() => {
  cargarEmpresas()
})
</script>