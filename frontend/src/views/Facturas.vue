<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-7xl mx-auto">
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-bold text-gray-800">Facturas Electrónicas (FEL)</h1>
        <button class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg shadow transition flex items-center gap-2">
          <span>+</span> Cargar XML
        </button>
      </div>

      <!-- FILTRO OBLIGATORIO -->
      <div class="bg-white p-4 rounded-lg shadow mb-6">
        <label class="block text-sm font-medium text-gray-700 mb-1">
          Empresa <span class="text-red-500">*</span>
        </label>
        <select
          v-model="selectedEmpresaId"
          @change="cargarFacturas"
          class="w-full md:w-1/2 border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 p-2 border"
        >
          <option value="">-- Seleccione una empresa para ver sus facturas --</option>
          <option v-for="emp in empresas" :key="emp.id" :value="emp.id">
            {{ emp.nombre }} ({{ emp.nit }})
          </option>
        </select>
      </div>

      <!-- ESTADO: Sin empresa seleccionada -->
      <div v-if="!selectedEmpresaId" class="bg-white rounded-lg shadow p-12 text-center border border-gray-200">
        <svg class="mx-auto h-16 w-16 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
        <p class="mt-4 text-gray-500 text-lg">Seleccione una empresa en el filtro superior para visualizar sus datos.</p>
      </div>

      <!-- TABLA DE RESULTADOS -->
      <div v-else class="bg-white rounded-lg shadow overflow-hidden">
        <!-- Loading Spinner -->
        <div v-if="loading" class="p-8 text-center">
          <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p class="mt-2 text-sm text-gray-500">Cargando facturas...</p>
        </div>

        <!-- Tabla -->
        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th @click="handleSort('numero')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none">
                  Factura {{ sortArrow('numero') }}
                </th>
                <th @click="handleSort('fecha_emision')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none">
                  Fecha {{ sortArrow('fecha_emision') }}
                </th>
                <th @click="handleSort('tipo_documento')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none">
                  Tipo DTE {{ sortArrow('tipo_documento') }}
                </th>
                <th @click="handleSort('tipo_operacion')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none">
                  Transacción {{ sortArrow('tipo_operacion') }}
                </th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Emisor/Receptor
                </th>
                <th @click="handleSort('es_exportacion')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none">
                  Ámbito {{ sortArrow('es_exportacion') }}
                </th>
                <th @click="handleSort('total_iva')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none">
                  IVA {{ sortArrow('total_iva') }}
                </th>
                <th @click="handleSort('tipo_cambio')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none">
                  T/C {{ sortArrow('tipo_cambio') }}
                </th>
                <th @click="handleSort('moneda')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none">
                  Moneda {{ sortArrow('moneda') }}
                </th>
                <th @click="handleSort('total')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none">
                  Total {{ sortArrow('total') }}
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="f in sortedFacturas" :key="f.id" class="hover:bg-gray-50 transition">
                <!-- Número de Factura (Link a detalle) -->
                <td class="px-4 py-3 text-sm">
                  <router-link 
                    :to="{ name: 'FacturaDetalle', params: { factura_id: f.id } }"
                    class="text-blue-600 hover:text-blue-800 font-mono font-semibold"
                  >
                    {{ f.serie }}-{{ f.numero }}
                  </router-link>
                </td>
                
                <td class="px-4 py-3 text-sm text-gray-600">{{ formatDate(f.fecha_emision) }}</td>
                
                <td class="px-4 py-3 text-sm">
                  <span :class="getTipoDTEClass(f.tipo_documento)" class="px-2 py-1 rounded text-xs font-semibold">
                    {{ f.tipo_documento || 'FACT' }}
                  </span>
                </td>
                
                <!-- Tipo de Transacción -->
                <td class="px-4 py-3 text-sm">
                  <span :class="f.tipo_operacion === 'Venta' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'" 
                        class="px-2 py-1 rounded text-xs font-semibold">
                    {{ f.tipo_operacion }}
                  </span>
                </td>
                
                <!-- Emisor/Receptor (dinámico según tipo) -->
                <td class="px-4 py-3 text-sm text-gray-700">
                  {{ f.tipo_operacion === 'Venta' ? f.receptor_nombre : f.emisor_nombre }}
                </td>
                
                <td class="px-4 py-3 text-sm">
                  <span :class="f.es_exportacion ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-700'" 
                        class="px-2 py-1 rounded text-xs font-semibold">
                    {{ f.es_exportacion ? 'Exportación' : 'Local' }}
                  </span>
                </td>
                
                <!-- IVA -->
                <td class="px-4 py-3 text-sm font-mono text-right">
                  {{ formatCurrency(f.total_iva, f.moneda) }}
                </td>
                
                <td class="px-4 py-3 text-sm font-mono text-gray-600">
                  {{ formatTipoCambio(f.tipo_cambio, f.moneda) }}
                </td>
                
                <td class="px-4 py-3 text-sm font-bold text-gray-700">{{ f.moneda }}</td>
                
                <td class="px-4 py-3 text-sm font-bold text-right text-gray-900">
                  {{ formatCurrency(f.total, f.moneda) }}
                </td>
              </tr>
              
              <tr v-if="sortedFacturas.length === 0">
                <td colspan="10" class="px-4 py-8 text-center text-gray-500">
                  No se encontraron facturas para esta empresa.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/services/api'
import { useRoute, useRouter } from 'vue-router'

const selectedEmpresaId = ref('')
const empresas = ref([])
const facturas = ref([])
const loading = ref(false)
const uploading = ref(false)
const statusMsg = ref('')
const statusType = ref('success')
const fileInput = ref(null)
const sortConfig = ref({ field: 'fecha_emision', direction: 'desc' })
const route = useRoute()
const router = useRouter()

// Formateadores
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('es-GT', { year: 'numeric', month: 'short', day: '2-digit' })
}

const formatTipoCambio = (tc, moneda) => {
  if (moneda === 'GTQ') return '1.00000'
  if (tc === null || tc === undefined) return 'N/A'
  return Number(tc).toFixed(5)
}

const formatCurrency = (amount, moneda) => {
  if (!amount) return '0.00'
  const symbol = moneda === 'GTQ' ? 'Q' : (moneda === 'USD' ? '$' : moneda)
  return `${symbol} ${Number(amount).toLocaleString('es-GT', { minimumFractionDigits: 2 })}`
}

const getTipoDTEClass = (codigo) => {
  const map = {
    FACT: 'bg-blue-100 text-blue-700',
    FCAM: 'bg-indigo-100 text-indigo-700',
    NCRE: 'bg-orange-100 text-orange-700',
    NDEB: 'bg-red-100 text-red-700',
    CIVA: 'bg-teal-100 text-teal-700',
    FESP: 'bg-pink-100 text-pink-700',
  }
  const base = 'px-2 py-1 rounded text-xs font-semibold'
  return `${base} ${map[codigo] || 'bg-gray-100 text-gray-700'}`
}

// Ordenamiento
const handleSort = (field) => {
  if (sortConfig.value.field === field) {
    sortConfig.value.direction = sortConfig.value.direction === 'asc' ? 'desc' : 'asc'
  } else {
    sortConfig.value.field = field
    sortConfig.value.direction = 'asc'
  }
}

const sortArrow = (field) => {
  if (sortConfig.value.field !== field) return ''
  return sortConfig.value.direction === 'asc' ? '▲' : '▼'
}

const sortedFacturas = computed(() => {
  const sorted = [...facturas.value]
  const { field, direction } = sortConfig.value
  if (!field) return sorted

  sorted.sort((a, b) => {
    let valA = a[field]
    let valB = b[field]

    if (field === 'fecha_emision') {
      valA = new Date(valA).getTime()
      valB = new Date(valB).getTime()
    } else if (typeof valA === 'boolean') {
      valA = valA ? 1 : 0
      valB = valB ? 1 : 0
    } else if (typeof valA === 'string') {
      valA = valA.toLowerCase()
      valB = valB.toLowerCase()
    } else if (valA === null || valA === undefined) {
      valA = direction === 'asc' ? -Infinity : Infinity
      valB = direction === 'asc' ? -Infinity : Infinity
    }

    if (valA < valB) return direction === 'asc' ? -1 : 1
    if (valA > valB) return direction === 'asc' ? 1 : -1
    return 0
  })
  return sorted
})

// Carga de datos
const cargarEmpresas = async () => {
  try {
    const { data } = await api.get('/empresas/')
    empresas.value = data
    // 🔹 Si viene un parámetro 'empresa' en la URL, selecciónalo
    if (route.query.empresa) {
      selectedEmpresaId.value = route.query.empresa
      await cargarFacturas()
    }
  } catch (err) {
    console.error('Error cargando empresas:', err)
  }
}

const cargarFacturas = async () => {
  if (!selectedEmpresaId.value) {
    facturas.value = []
    return
  }

  loading.value = true
  try {
    const { data } = await api.get('/facturas/', {
      params: { empresa_id: selectedEmpresaId.value }
    })
    facturas.value = data
  } catch (err) {
    console.error('Error cargando facturas:', err)
  } finally {
    loading.value = false
  }
}

// Manejo de archivos
const handleFileSelect = async (event) => {
  const files = Array.from(event.target.files)
  if (files.length === 0) return

  const xmlFiles = files.filter(f => f.name.toLowerCase().endsWith('.xml'))
  if (xmlFiles.length !== files.length) {
    statusMsg.value = '⚠️ Solo se permiten archivos .xml'
    statusType.value = 'error'
    event.target.value = ''
    return
  }

  if (!selectedEmpresaId.value) {
    statusMsg.value = '⚠️ Selecciona una empresa antes de cargar'
    statusType.value = 'error'
    return
  }

  await uploadFacturas(xmlFiles)
  event.target.value = ''
}

const uploadFacturas = async (files) => {
  uploading.value = true
  statusMsg.value = ''
  
  try {
    const formData = new FormData()
    files.forEach(file => formData.append('files', file))

    // Axios detecta FormData y ajusta Content-Type automáticamente
    const { data } = await api.post('/facturas/upload', formData, {
      params: { empresa_id: selectedEmpresaId.value },
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    const msg = data.rechazadas?.length 
      ? `✅ ${data.cargadas} cargadas. ⚠️ ${data.rechazadas.length} rechazadas.` 
      : `✅ ${data.cargadas} facturas cargadas correctamente.`
    
    statusMsg.value = msg
    statusType.value = 'success'
    await cargarFacturas()
  } catch (err) {
    const detail = err.response?.data?.detail || err.message || 'Error al procesar los archivos'
    statusMsg.value = `❌ ${detail}`
    statusType.value = 'error'
    console.error('Error en upload:', err)
  } finally {
    uploading.value = false
  }
}

onMounted(() => {
  cargarEmpresas()
})
</script>