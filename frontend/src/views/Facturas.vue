<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold">Facturas Electrónicas (FEL)</h2>
      <label class="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600 cursor-pointer transition">
        Cargar XML
        <input type="file" multiple accept=".xml" class="hidden" @change="handleUpload" ref="fileInput" />
      </label>
    </div>

    <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">{{ error }}</div>
    <div v-if="exito" class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">{{ exito }}</div>

    <!-- Filtro por empresa -->
    <div class="bg-white shadow-md rounded-lg p-4 mb-4 flex gap-4 items-end">
      <div class="flex-1">
        <label class="block text-gray-700 text-sm font-bold mb-2">Filtrar por Empresa</label>
        <select v-model="empresaFiltro" @change="cargarFacturas" class="w-full px-3 py-2 border rounded-md">
          <option value="">Todas las empresas</option>
          <option v-for="emp in empresas" :key="emp.id" :value="emp.id">{{ emp.nombre }}</option>
        </select>
      </div>
      <div class="flex-1">
        <label class="block text-gray-700 text-sm font-bold mb-2">Buscar</label>
        <input v-model="busqueda" type="text" placeholder="Buscar por autorización, emisor..." class="w-full px-3 py-2 border rounded-md" @input="cargarFacturas" />
      </div>
    </div>

    <!-- Tabla de facturas -->
    <div v-if="cargando" class="text-center py-8 text-gray-500">Cargando facturas...</div>
    <div v-else-if="facturasFiltradas.length === 0" class="bg-white shadow-md rounded-lg p-8 text-center text-gray-500">
      No se encontraron facturas.
    </div>
    <div v-else class="bg-white shadow-md rounded-lg overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th @click="toggleOrder('numero_autorizacion')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer select-none hover:bg-gray-100">
              Autorización {{ sortIcon('numero_autorizacion') }}
            </th>
            <th @click="toggleOrder('numero')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer select-none hover:bg-gray-100">
              Número {{ sortIcon('numero') }}
            </th>
            <th @click="toggleOrder('fecha_emision')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer select-none hover:bg-gray-100">
              Fecha {{ sortIcon('fecha_emision') }}
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Moneda</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Emisor</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total IVA</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="f in facturasFiltradas" :key="f.id" class="hover:bg-gray-50">
            <td class="px-4 py-3 text-sm font-mono">{{ f.numero_autorizacion }}</td>
            <td class="px-4 py-3 text-sm font-mono text-blue-600 hover:text-blue-800">
              <router-link :to="`/dashboard/facturas/${f.id}?empresa=${empresaFiltro}`">
                {{ f.serie }} {{ f.numero }}
              </router-link>
            </td>
            <td class="px-4 py-3 text-sm">{{ formatearFecha(f.fecha_emision) }}</td>
            <td class="px-4 py-3 text-sm">{{ f.es_exportacion ? 'E' : (f.tipo_documento || 'L') }}</td>
            <td class="px-4 py-3 text-sm">{{ f.moneda }}</td>
            <td class="px-4 py-3 text-sm">{{ f.emisor_nombre }}</td>
            <td class="px-4 py-3 text-sm text-right">{{ f.moneda }} {{ f.total_iva }}</td>
            <td class="px-4 py-3 text-sm text-right">{{ f.moneda }} {{ f.total }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'

const route = useRoute()
const router = useRouter()

const facturas = ref([])
const empresas = ref([])
const empresaFiltro = ref(route.query.empresa || '')
const busqueda = ref('')
const cargando = ref(false)
const error = ref('')
const exito = ref('')
const fileInput = ref(null)

const orderField = ref('fecha_emision')
const orderDir = ref('desc')

const facturasFiltradas = computed(() => {
  let resultado = [...facturas.value]
  if (busqueda.value.trim()) {
    const term = busqueda.value.toLowerCase()
    resultado = resultado.filter(f =>
      f.numero_autorizacion?.toLowerCase().includes(term) ||
      f.emisor_nombre?.toLowerCase().includes(term) ||
      f.receptor_nombre?.toLowerCase().includes(term) ||
      (f.serie + ' ' + f.numero).toLowerCase().includes(term)
    )
  }
  // Ordenamiento
  resultado.sort((a, b) => {
    let valA = a[orderField.value]
    let valB = b[orderField.value]
    if (orderField.value === 'fecha_emision') {
      valA = new Date(valA)
      valB = new Date(valB)
    } else {
      valA = (valA || '').toString()
      valB = (valB || '').toString()
    }
    if (valA < valB) return orderDir.value === 'asc' ? -1 : 1
    if (valA > valB) return orderDir.value === 'asc' ? 1 : -1
    return 0
  })
  return resultado
})

function toggleOrder(field) {
  if (orderField.value === field) {
    orderDir.value = orderDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    orderField.value = field
    orderDir.value = 'asc'
  }
}

function sortIcon(field) {
  if (orderField.value !== field) return '↕'
  return orderDir.value === 'asc' ? '↑' : '↓'
}

function formatearFecha(fecha) {
  if (!fecha) return ''
  return fecha.includes('T') ? fecha.split('T')[0] : fecha.substring(0, 10)
}

async function cargarEmpresas() {
  const resp = await api.get('/empresas/')
  empresas.value = resp.data
}

async function cargarFacturas() {
  cargando.value = true
  try {
    const params = {}
    if (empresaFiltro.value) params.empresa_id = empresaFiltro.value
    const resp = await api.get('/facturas/', { params })
    facturas.value = resp.data
  } catch (err) {
    error.value = 'Error al cargar facturas'
  } finally {
    cargando.value = false
  }
}

async function handleUpload(event) {
  const files = event.target.files
  if (!files.length) return
  if (!empresaFiltro.value) {
    error.value = 'Debe seleccionar una empresa antes de cargar facturas'
    return
  }
  const formData = new FormData()
  for (const file of files) formData.append('files', file)
  cargando.value = true
  try {
    const resp = await api.post(`/facturas/upload?empresa_id=${empresaFiltro.value}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    const count = Array.isArray(resp.data) ? resp.data.length : 1
    exito.value = `${count} factura(s) cargada(s) correctamente`
    fileInput.value.value = ''
    await cargarFacturas()
    setTimeout(() => { exito.value = '' }, 5000)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al cargar facturas'
  } finally {
    cargando.value = false
  }
}

onMounted(() => {
  cargarEmpresas()
  cargarFacturas()
})
</script>