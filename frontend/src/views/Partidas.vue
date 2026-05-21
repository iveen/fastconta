<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold">Partidas Contables</h2>
      <button
        @click="mostrarFormulario = !mostrarFormulario"
        class="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600 transition"
      >
        {{ mostrarFormulario ? 'Cancelar' : 'Nueva Partida' }}
      </button>
    </div>

    <!-- Mensaje de error -->
    <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
      {{ error }}
    </div>

    <!-- Filtros y búsqueda -->
    <div class="bg-white shadow-md rounded-lg p-4 mb-4 grid grid-cols-1 md:grid-cols-3 gap-4">
      <div>
        <label class="block text-gray-700 text-sm font-bold mb-2">Filtrar por Empresa</label>
        <select
          v-model="empresaFiltroId"
          @change="cargarPartidas"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Todas las empresas</option>
          <option v-for="emp in empresas" :key="emp.id" :value="emp.id">
            {{ emp.nombre }}
          </option>
        </select>
      </div>
      <div class="md:col-span-2">
        <label class="block text-gray-700 text-sm font-bold mb-2">Buscar</label>
        <input
          v-model="busqueda"
          type="text"
          placeholder="Buscar por póliza, descripción o fecha..."
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
    </div>

    <!-- Formulario de creación -->
    <div v-if="mostrarFormulario" class="bg-white shadow-md rounded-lg p-6 mb-6">
      <h3 class="text-lg font-semibold mb-4">Nueva Partida</h3>
      <form @submit.prevent="crearPartida">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label class="block text-gray-700 text-sm font-bold mb-2">Fecha</label>
            <input
              v-model="nuevaPartida.fecha"
              type="date"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label class="block text-gray-700 text-sm font-bold mb-2">Número Póliza (opcional)</label>
            <input
              v-model="nuevaPartida.numero_poliza"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Auto-generado"
            />
          </div>
        </div>
        <div class="mb-4">
          <label class="block text-gray-700 text-sm font-bold mb-2">Descripción</label>
          <textarea
            v-model="nuevaPartida.descripcion"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows="2"
            required
          ></textarea>
        </div>

        <!-- Detalles -->
        <div class="mb-4">
          <div class="flex justify-between items-center mb-2">
            <h4 class="font-semibold text-gray-700">Detalles</h4>
            <button
              type="button"
              @click="agregarDetalle"
              class="text-blue-500 hover:text-blue-700 text-sm"
            >
              + Agregar línea
            </button>
          </div>
          <div v-for="(detalle, index) in nuevaPartida.detalles" :key="index" class="flex gap-2 mb-2 items-start">
            <div class="flex-1">
              <select
                v-model="detalle.cuenta_id"
                class="w-full px-2 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                <option value="">Seleccionar cuenta</option>
                <option v-for="c in cuentasDisponibles" :key="c.id" :value="c.id">
                  {{ c.codigo }} - {{ c.nombre }}
                </option>
              </select>
            </div>
            <div class="w-24">
              <select
                v-model="detalle.tipo_movimiento"
                class="w-full px-2 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                <option value="debe">Debe</option>
                <option value="haber">Haber</option>
              </select>
            </div>
            <div class="w-32">
              <input
                v-model.number="detalle.monto"
                type="number"
                step="0.01"
                min="0.01"
                class="w-full px-2 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Monto"
                required
              />
            </div>
            <button
              type="button"
              @click="eliminarDetalle(index)"
              class="text-red-500 hover:text-red-700 text-sm mt-2"
            >
              ✕
            </button>
          </div>
        </div>

        <button
          type="submit"
          :disabled="cargando"
          class="bg-green-500 text-white px-6 py-2 rounded-md hover:bg-green-600 transition disabled:opacity-50"
        >
          {{ cargando ? 'Creando...' : 'Crear Partida' }}
        </button>
      </form>
    </div>

    <!-- Tabla de partidas -->
    <div v-if="cargandoLista" class="text-center py-8 text-gray-500">
      Cargando partidas...
    </div>
    <div v-else-if="partidasFiltradas.length === 0" class="bg-white shadow-md rounded-lg p-8 text-center text-gray-500">
      No se encontraron partidas.
    </div>
    <div v-else class="bg-white shadow-md rounded-lg overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer select-none"
                @click="toggleOrder('numero_poliza')">
              Póliza {{ sortIcon('numero_poliza') }}
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer select-none"
                @click="toggleOrder('fecha')">
              Fecha {{ sortIcon('fecha') }}
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Descripción
            </th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              Debe
            </th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              Haber
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="p in partidasFiltradas" :key="p.id" class="hover:bg-gray-50">
            <td class="px-4 py-3 whitespace-nowrap text-sm font-mono text-blue-600 hover:text-blue-800">
              <router-link :to="`/dashboard/partidas/${p.id}`">
                {{ p.numero_poliza || 'S/N' }}
              </router-link>
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">
              {{ p.fecha }}
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">
              {{ p.descripcion }}
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-900">
              {{ calcularTotal(p.detalles, 'debe') }}
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-900">
              {{ calcularTotal(p.detalles, 'haber') }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '@/services/api'

const empresas = ref([])
const empresaFiltroId = ref('')
const partidas = ref([])
const cuentasDisponibles = ref([])
const mostrarFormulario = ref(false)
const cargando = ref(false)
const cargandoLista = ref(false)
const error = ref('')
const busqueda = ref('')
const orderField = ref('fecha')
const orderDirection = ref('desc')

const nuevaPartida = ref({
  fecha: '',
  descripcion: '',
  numero_poliza: '',
  detalles: []
})

// Datos filtrados y ordenados
const partidasFiltradas = computed(() => {
  let resultado = [...partidas.value]

  // Filtro por búsqueda
  if (busqueda.value.trim()) {
    const termino = busqueda.value.toLowerCase()
    resultado = resultado.filter(p =>
      (p.numero_poliza && p.numero_poliza.toLowerCase().includes(termino)) ||
      p.descripcion.toLowerCase().includes(termino) ||
      p.fecha.includes(termino)
    )
  }

  // Ordenamiento
  resultado.sort((a, b) => {
    let valA = a[orderField.value]
    let valB = b[orderField.value]
    if (orderField.value === 'fecha') {
      valA = new Date(valA)
      valB = new Date(valB)
    }
    if (orderField.value === 'numero_poliza') {
      valA = valA || ''
      valB = valB || ''
      return orderDirection.value === 'asc' 
        ? valA.localeCompare(valB) 
        : valB.localeCompare(valA)
    }
    if (valA < valB) return orderDirection.value === 'asc' ? -1 : 1
    if (valA > valB) return orderDirection.value === 'asc' ? 1 : -1
    return 0
  })

  return resultado
})

function toggleOrder(field) {
  if (orderField.value === field) {
    orderDirection.value = orderDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    orderField.value = field
    orderDirection.value = 'asc'
  }
}

function sortIcon(field) {
  if (orderField.value !== field) return '↕'
  return orderDirection.value === 'asc' ? '↑' : '↓'
}

function calcularTotal(detalles, tipo) {
  if (!detalles) return '0.00'
  const suma = detalles
    .filter(d => d.tipo_movimiento === tipo)
    .reduce((acc, d) => acc + parseFloat(d.monto), 0)
  return suma.toFixed(2)
}

async function cargarEmpresas() {
  try {
    const response = await api.get('/empresas/')
    empresas.value = response.data
  } catch (err) {
    error.value = 'Error al cargar empresas'
  }
}

async function cargarCuentas() {
  try {
    const response = await api.get('/plan-cuentas/')
    cuentasDisponibles.value = response.data
  } catch (err) {
    error.value = 'Error al cargar cuentas'
  }
}

async function cargarPartidas() {
  cargandoLista.value = true
  error.value = ''
  try {
    const params = {}
    if (empresaFiltroId.value) {
      params.empresa_id = empresaFiltroId.value
    }
    const response = await api.get('/partidas/', { params })
    partidas.value = response.data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al cargar partidas'
  } finally {
    cargandoLista.value = false
  }
}

function agregarDetalle() {
  nuevaPartida.value.detalles.push({
    cuenta_id: '',
    tipo_movimiento: 'debe',
    monto: null
  })
}

function eliminarDetalle(index) {
  nuevaPartida.value.detalles.splice(index, 1)
}

async function crearPartida() {
  cargando.value = true
  error.value = ''
  try {
    await api.post('/partidas/', {
      fecha: nuevaPartida.value.fecha,
      descripcion: nuevaPartida.value.descripcion,
      numero_poliza: nuevaPartida.value.numero_poliza || null,
      detalles: nuevaPartida.value.detalles.map(d => ({
        cuenta_id: d.cuenta_id,
        tipo_movimiento: d.tipo_movimiento,
        monto: d.monto
      }))
    })
    nuevaPartida.value = { fecha: '', descripcion: '', numero_poliza: '', detalles: [] }
    mostrarFormulario.value = false
    await cargarPartidas()
  } catch (err) {
    const detail = err.response?.data?.detail
    if (Array.isArray(detail)) {
      error.value = detail.map(e => e.msg).join(', ')
    } else {
      error.value = detail || 'Error al crear partida'
    }
  } finally {
    cargando.value = false
  }
}

onMounted(() => {
  cargarEmpresas()
  cargarCuentas()
  cargarPartidas()
})
</script>