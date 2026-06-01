<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header con botones de carga -->
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-bold text-gray-800">Facturas Electrónicas (FEL)</h1>
        <div class="flex gap-3">
          <!-- Carga XML (existente) -->
          <input ref="fileXML" type="file" multiple accept=".xml" @change="handleFileSelect" class="hidden" />
          <button @click="$refs.fileXML.click()" :disabled="!selectedEmpresaId || uploading" 
            class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg shadow transition flex items-center gap-2 disabled:opacity-50">
            <span>+</span> {{ uploading ? 'Subiendo...' : 'Cargar XML' }}
          </button>

          <!-- ✅ NUEVO: Validación Hoja Electrónica -->
          <input ref="fileXLS" type="file" accept=".xlsx,.xls" @change="validarXLS" class="hidden" />
          <button @click="$refs.fileXLS.click()" :disabled="!selectedEmpresaId || validando" 
            class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg shadow transition flex items-center gap-2 disabled:opacity-50">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {{ validando ? 'Validando...' : 'Validar Hoja' }}
          </button>
        </div>
      </div>

      <!-- Banner de estado -->
      <div v-if="statusMsg" :class="statusType === 'error' ? 'bg-red-100 border-red-400 text-red-700' : 'bg-green-100 border-green-400 text-green-700'" 
           class="border px-4 py-3 rounded mb-6 flex justify-between items-center">
        <span>{{ statusMsg }}</span>
        <button @click="statusMsg = ''" class="text-sm underline hover:no-underline">Cerrar</button>
      </div>

      <!-- Filtro de empresa -->
      <div class="bg-white p-4 rounded-lg shadow mb-6">
        <label class="block text-sm font-medium text-gray-700 mb-1">
          Empresa <span class="text-red-500">*</span>
        </label>
        <select v-model="selectedEmpresaId" @change="cargarFacturas" 
          class="w-full md:w-1/2 border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 p-2 border">
          <option value="">-- Seleccione una empresa para ver sus facturas --</option>
          <option v-for="emp in empresas" :key="emp.id" :value="emp.id">
            {{ emp.nombre }} ({{ emp.nit }})
          </option>
        </select>
      </div>

      <!-- Estado vacío -->
      <div v-if="!selectedEmpresaId" class="bg-white rounded-lg shadow p-12 text-center border border-gray-200">
        <svg class="mx-auto h-16 w-16 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
        <p class="mt-4 text-gray-500 text-lg">Seleccione una empresa en el filtro superior para visualizar sus datos.</p>
      </div>

      <!-- Tabla de resultados -->
      <div v-else class="bg-white rounded-lg shadow overflow-hidden">
        <div v-if="loading" class="p-8 text-center">
          <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p class="mt-2 text-sm text-gray-500">Cargando facturas...</p>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th @click="handleSort('fecha_emision')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none">
                  Fecha {{ sortArrow('fecha_emision') }}
                </th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo DTE</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">DTE</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Transacción</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Emisor/Receptor</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ámbito / Estado</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">IVA</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">T/C</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Moneda</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Total</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Validación</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="f in sortedFacturas" :key="f.id" 
                  :class="['hover:bg-gray-50 transition', f.estado === 'Anulada' ? 'bg-red-50' : '']">
                <td class="px-4 py-3 text-sm text-gray-600">{{ formatDate(f.fecha_emision) }}</td>
                
                <td class="px-4 py-3 text-sm">
                  <span :class="getTipoDTEClass(f.tipo_documento)" class="px-2 py-1 rounded text-xs font-semibold">
                    {{ f.tipo_documento || 'FACT' }}
                  </span>
                </td>

                <td class="px-4 py-3 text-sm">
                  <router-link
                    :to="{ name: 'FacturaDetalle', params: { factura_id: f.id }, query: { empresa: selectedEmpresaId } }"
                    class="text-blue-600 hover:text-blue-800 font-mono font-semibold"
                  >
                    {{ f.serie || 'S/N' }}-{{ f.numero || '000' }}
                  </router-link>
                </td>
                
                <td class="px-4 py-3 text-sm">
                  <span :class="f.tipo_operacion === 'Venta' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'" 
                        class="px-2 py-1 rounded text-xs font-semibold">
                    {{ f.tipo_operacion }}
                  </span>
                </td>
                
                <td class="px-4 py-3 text-sm text-gray-700 truncate max-w-xs">
                  {{ f.tipo_operacion === 'Venta' ? f.receptor_nombre : f.emisor_nombre }}
                </td>
                
                <!-- ✅ Badge dinámico: Anulada vs Ámbito -->
                <td class="px-4 py-3 text-sm">
                  <span v-if="f.estado === 'Anulada'" 
                        class="px-2 py-1 rounded text-xs font-bold bg-red-100 text-red-700 border border-red-200">
                    ANULADA
                  </span>
                  <span v-else 
                        :class="f.es_exportacion ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-700'" 
                        class="px-2 py-1 rounded text-xs font-semibold">
                    {{ f.es_exportacion ? 'Exportación' : 'Local' }}
                  </span>
                </td>
                
                <td class="px-4 py-3 text-sm font-mono text-right">{{ formatCurrency(f.total_iva, f.moneda) }}</td>
                <td class="px-4 py-3 text-sm font-mono text-gray-600">{{ formatTipoCambio(f.tipo_cambio, f.moneda) }}</td>
                <td class="px-4 py-3 text-sm font-bold text-gray-700">{{ f.moneda }}</td>
                <td class="px-4 py-3 text-sm font-bold text-right text-gray-900">{{ formatCurrency(f.total, f.moneda) }}</td>
                <td class="px-4 py-3 text-sm">
                  <div v-if="f.validado" class="flex flex-col items-start gap-1">
                    <span class="px-2 py-1 rounded text-xs font-bold bg-green-100 text-green-700 border border-green-200">
                      ✅ Validada
                    </span>
                    <span v-if="f.fecha_validacion" class="text-[10px] text-gray-500">
                      {{ formFechaValidacion(f.fecha_validacion) }}
                    </span>
                  </div>
                  <span v-else class="px-2 py-1 rounded text-xs font-bold bg-gray-100 text-gray-600 border border-gray-200">
                    ❌ Pendiente
                  </span>
                </td>
              </tr>
              
              <tr v-if="sortedFacturas.length === 0">
                <td colspan="9" class="px-4 py-8 text-center text-gray-500">
                  No se encontraron facturas para esta empresa.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ✅ MODAL: Resultados de validación XLS -->
    <div v-if="resultadoXLS" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-lg shadow-xl max-w-lg w-full p-6">
        <h3 class="text-lg font-bold mb-2" :class="resultadoXLS.success ? 'text-green-600' : 'text-red-600'">
          {{ resultadoXLS.success ? '✅ Validación Exitosa' : '⚠️ Validación Rechazada' }}
        </h3>
        <p class="text-gray-600 mb-4">{{ resultadoXLS.mensaje }}</p>
        <ul v-if="resultadoXLS.pendientes?.length" class="bg-gray-50 p-3 rounded text-sm font-mono text-red-700 max-h-40 overflow-y-auto mb-4">
          <li v-for="p in resultadoXLS.pendientes" :key="p">• {{ p }}</li>
        </ul>
        <button @click="resultadoXLS = null" class="w-full bg-gray-200 hover:bg-gray-300 text-gray-800 py-2 rounded font-medium">Cerrar</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/services/api'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const selectedEmpresaId = ref(route.query.empresa || '')
const empresas = ref([])
const facturas = ref([])
const loading = ref(false)
const uploading = ref(false)
const statusMsg = ref('')
const statusType = ref('success')
const fileXML = ref(null)

// ✅ NUEVO: Estados para validación XLS
const fileXLS = ref(null)
const validando = ref(false)
const resultadoXLS = ref(null)

const sortConfig = ref({ field: 'fecha_emision', direction: 'desc' })

// Formateadores
const formatDate = (dateStr) => dateStr ? new Date(dateStr).toLocaleDateString('es-GT', { year: 'numeric', month: 'short', day: '2-digit' }) : '-'
const formatTipoCambio = (tc, moneda) => moneda === 'GTQ' ? '1.00000' : (tc ? Number(tc).toFixed(5) : 'N/A')
const formatCurrency = (amount, moneda) => {
  if (!amount) return '0.00'
  const symbol = moneda === 'GTQ' ? 'Q' : (moneda === 'USD' ? '$' : moneda)
  return `${symbol} ${Number(amount).toLocaleString('es-GT', { minimumFractionDigits: 2 })}`
}
const getTipoDTEClass = (codigo) => {
  const map = {
    FACT: 'bg-blue-100 text-blue-700', FCAM: 'bg-indigo-100 text-indigo-700',
    NCRE: 'bg-orange-100 text-orange-700', NDEB: 'bg-red-100 text-red-700',
    CIVA: 'bg-teal-100 text-teal-700', FESP: 'bg-pink-100 text-pink-700'
  }
  return `px-2 py-1 rounded text-xs font-semibold ${map[codigo] || 'bg-gray-100 text-gray-700'}`
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
const sortArrow = (field) => sortConfig.value.field === field ? (sortConfig.value.direction === 'asc' ? '▲' : '▼') : ''
const sortedFacturas = computed(() => {
  const sorted = [...facturas.value]
  const { field, direction } = sortConfig.value
  if (!field) return sorted
  sorted.sort((a, b) => {
    let valA = a[field], valB = b[field]
    if (field === 'fecha_emision') { valA = new Date(valA).getTime(); valB = new Date(valB).getTime() }
    else if (typeof valA === 'boolean') { valA = valA ? 1 : 0; valB = valB ? 1 : 0 }
    else if (typeof valA === 'string') { valA = valA.toLowerCase(); valB = valB.toLowerCase() }
    else if (valA === null || valA === undefined) { valA = direction === 'asc' ? -Infinity : Infinity; valB = valA }
    return valA < valB ? (direction === 'asc' ? -1 : 1) : valA > valB ? (direction === 'asc' ? 1 : -1) : 0
  })
  return sorted
})

// Carga de datos
const cargarEmpresas = async () => {
  try {
    const { data } = await api.get('/empresas/')
    empresas.value = data
    if (route.query.empresa) {
      selectedEmpresaId.value = route.query.empresa
      await cargarFacturas()
    }
  } catch (err) { console.error('Error cargando empresas:', err) }
}

const formFechaValidacion = (d) => d 
  ? new Date(d).toLocaleString('es-GT', { dateStyle: 'short', timeStyle: 'short' }) 
  : ''

const cargarFacturas = async () => {
  if (!selectedEmpresaId.value) { facturas.value = []; return }
  loading.value = true
  try {
    const { data } = await api.get('/facturas/', { params: { empresa_id: selectedEmpresaId.value } })
    facturas.value = data
  } catch (err) { console.error('Error cargando facturas:', err) }
  finally { loading.value = false }
}

// Manejo de archivos XML
const handleFileSelect = async (event) => {
  const files = Array.from(event.target.files).filter(f => f.name.toLowerCase().endsWith('.xml'))
  if (!files.length) return
  if (!selectedEmpresaId.value) { statusMsg.value = '️ Selecciona una empresa antes de cargar'; statusType.value = 'error'; return }
  await uploadFacturas(files)
  event.target.value = ''
}
const uploadFacturas = async (files) => {
  uploading.value = true; statusMsg.value = ''
  try {
    const formData = new FormData()
    files.forEach(file => formData.append('files', file))
    const { data } = await api.post('/facturas/upload', formData, { params: { empresa_id: selectedEmpresaId.value }, headers: {'Content-Type': undefined} })
    const msg = data.rechazadas?.length 
      ? `✅ ${data.cargadas} cargadas. ⚠️ ${data.rechazadas.length} rechazadas.` 
      : `✅ ${data.cargadas} facturas cargadas correctamente.`
    statusMsg.value = msg; statusType.value = 'success'
    await cargarFacturas()
  } catch (err) {
    statusMsg.value = `❌ ${err.response?.data?.detail || err.message}`; statusType.value = 'error'
  } finally { uploading.value = false }
}

// ✅ NUEVO: Validación Hoja Electrónica
const validarXLS = async (e) => {
  const file = e.target.files[0]
  if (!file || !selectedEmpresaId.value) return
  validando.value = true; resultadoXLS.value = null
  try {
    const fd = new FormData()
    fd.append('file', file)
    const { data } = await api.post('/facturas/validar-hoja-electronica', fd, {
      params: { empresa_id: selectedEmpresaId.value },
      headers: {
        'Content-Type': undefined
      } // Deja que Axios calcule el boundary correctamente
    })
    resultadoXLS.value = data
    if (data.success) await cargarFacturas()
  } catch (err) {
    resultadoXLS.value = { success: false, mensaje: err.response?.data?.detail || 'Error de conexión' }
  } finally {
    validando.value = false; e.target.value = ''
  }
}

// Sincronización URL
watch(selectedEmpresaId, (val) => {
  if (val) router.replace({ query: { ...route.query, empresa: val } })
  else router.replace({ query: { ...route.query, empresa: undefined } })
})

onMounted(() => { cargarEmpresas() })
</script>