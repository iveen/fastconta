<!-- src/views/Facturas.vue -->
<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-bold text-gray-800">Facturas Electrónicas (FEL)</h1>
        <div class="flex gap-3">
          <input ref="fileXML" type="file" multiple accept=".xml,.pdf" @change="handleFileSelect" class="hidden" />
          <button
            @click="$refs.fileXML.click()"
            :disabled="!companyStore.selectedCompanyId || uploading"
            class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg shadow transition flex items-center gap-2 disabled:opacity-50 relative group"
            title="Soporta XML y PDF (con XML embebido)"
          >
            <span>+</span> {{ uploading ? 'Subiendo...' : 'Cargar FEL' }}
            <span class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 text-xs bg-gray-800 text-white rounded opacity-0 group-hover:opacity-100 transition whitespace-nowrap pointer-events-none">
              Formatos: XML, PDF
            </span>
          </button>
          <input ref="fileXLS" type="file" accept=".xlsx,.xls" @change="validarXLS" class="hidden" />
          <button @click="$refs.fileXLS.click()" :disabled="!companyStore.selectedCompanyId || validando" class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg shadow transition flex items-center gap-2 disabled:opacity-50">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            {{ validando ? 'Validando...' : 'Validar Hoja' }}
          </button>
        </div>
      </div>

      <!-- Banner de estado -->
      <div v-if="statusMsg" :class="statusType === 'error' ? 'bg-red-100 border-red-400 text-red-700' : 'bg-green-100 border-green-400 text-green-700'" class="border px-4 py-3 rounded mb-6 flex justify-between items-center">
        <span>{{ statusMsg }}</span>
        <button @click="statusMsg = ''" class="text-sm underline hover:no-underline">Cerrar</button>
      </div>

      <!-- 🔹 SELECTOR DE TENANT (Solo Superadmin) -->
      <div v-if="authStore.isSuperAdmin" class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <label class="block text-sm font-semibold text-blue-800 mb-1">🏢 Seleccionar Firma (Tenant)</label>
        <select v-model="selectedTenantId" @change="handleTenantChange" class="w-full md:w-1/2 border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 p-2 border bg-white">
          <option value="">-- Seleccione una firma --</option>
          <option v-for="t in tenants" :key="t.id" :value="t.id">{{ t.name }} ({{ t.nit }})</option>
        </select>
      </div>

      <!-- ✅ MENSAJE SI NO HAY EMPRESA SELECCIONADA -->
      <div v-if="!companyStore.selectedCompanyId" class="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-12 rounded-lg text-center">
        <svg class="w-12 h-12 mx-auto mb-3 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
        <p class="text-lg font-semibold">Selecciona una empresa desde la barra superior para visualizar las facturas electrónicas</p>
      </div>

      <!-- ✅ CONTENIDO PRINCIPAL (solo si hay empresa seleccionada) -->
      <div v-else>
        <!-- Info de empresa activa -->
        <div class="bg-white p-4 rounded-lg shadow mb-6 flex items-center gap-2">
          <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
          <span class="text-sm text-gray-600">Empresa:</span>
          <span class="font-semibold text-gray-800">{{ companyStore.currentCompany?.nombre || 'Desconocida' }}</span>
        </div>

        <!--  TARJETAS DE RESUMEN -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p class="text-sm text-blue-600 font-medium">Compras del Período</p>
            <p class="text-2xl font-bold text-blue-700">{{ formatCurrency(totalesCompras, 'GTQ') }}</p>
            <p class="text-xs text-blue-600 mt-1">{{ facturasFiltradas.filter(f => f.tipo_operacion === 'Compra').length }} facturas recibidas</p>
          </div>
          
          <div class="bg-green-50 border border-green-200 rounded-lg p-4">
            <p class="text-sm text-green-600 font-medium">Ventas del Período</p>
            <p class="text-2xl font-bold text-green-700">{{ formatCurrency(totalesVentas, 'GTQ') }}</p>
            <p class="text-xs text-green-600 mt-1">{{ facturasFiltradas.filter(f => f.tipo_operacion === 'Venta').length }} facturas emitidas</p>
          </div>
          
          <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <p class="text-sm text-gray-600 font-medium">Balance Neto</p>
            <p class="text-2xl font-bold" :class="totalesVentas - totalesCompras >= 0 ? 'text-green-700' : 'text-red-700'">
              {{ formatCurrency(totalesVentas - totalesCompras, 'GTQ') }}
            </p>
            <p class="text-xs text-gray-600 mt-1">Ventas - Compras</p>
          </div>
        </div>

        <!-- 🆕 FILTROS DE PERÍODO -->
        <div class="bg-white p-4 rounded-lg shadow mb-6 flex flex-wrap items-center gap-4">
          <div class="flex items-center gap-2">
            <label class="text-sm font-medium text-gray-700">Período:</label>
            <select v-model="filtroMes" @change="aplicarFiltros" class="border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 p-2 border text-sm">
              <option value="">Todos los meses</option>
              <option v-for="m in meses" :key="m.value" :value="m.value">{{ m.label }}</option>
            </select>
          </div>
          
          <div class="flex items-center gap-2">
            <label class="text-sm font-medium text-gray-700">Año:</label>
            <select v-model="filtroAnio" @change="aplicarFiltros" class="border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 p-2 border text-sm">
              <option value="">Todos los años</option>
              <option v-for="a in anios" :key="a" :value="a">{{ a }}</option>
            </select>
          </div>
          
          <button 
            v-if="filtroMes || filtroAnio" 
            @click="limpiarFiltros" 
            class="text-sm text-blue-600 hover:text-blue-800 underline"
          >
            Limpiar filtros
          </button>
          
          <div class="ml-auto text-sm text-gray-600">
            Mostrando {{ facturasFiltradas.length }} de {{ facturas.length }} facturas
          </div>
        </div>

        <!-- Tabla de resultados -->
        <div class="bg-white rounded-lg shadow overflow-hidden">
          <div v-if="loading" class="p-8 text-center">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p class="mt-2 text-sm text-gray-500">Cargando facturas...</p>
          </div>
          <div v-else class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th @click="handleSort('fecha_emision')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none">Fecha {{ sortArrow('fecha_emision') }}</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo DTE</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">DTE</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Transacción</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Emisor/Receptor</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ámbito / Estado</th>
                  <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">IVA</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">T/C</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Moneda</th>
                  <th class="px-4 py-3 text-right text-xs font-medium text-blue-600 uppercase tracking-wider">Compras</th>
                  <th class="px-4 py-3 text-right text-xs font-medium text-green-600 uppercase tracking-wider">Ventas</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Validación</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="f in sortedFacturas" :key="f.id" :class="['hover:bg-gray-50 transition', f.estado === 'Anulada' ? 'bg-red-50' : '']">
                  <td class="px-4 py-3 text-sm text-gray-600">{{ formatDateGT(f.fecha_emision) }}</td>
                  <td class="px-4 py-3 text-sm"><span :class="getTipoDTEClass(f.tipo_documento)" class="px-2 py-1 rounded text-xs font-semibold">{{ f.tipo_documento || 'FACT' }}</span></td>
                  <td class="px-4 py-3 text-sm">
                    <router-link :to="{ name: 'FacturaDetalle', params: { factura_id: f.id } }" class="text-blue-600 hover:text-blue-800 font-mono font-semibold">
                      {{ f.serie || 'S/N' }}-{{ f.numero || '000' }}
                    </router-link>
                  </td>
                  <td class="px-4 py-3 text-sm"><span :class="f.tipo_operacion === 'Venta' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'" class="px-2 py-1 rounded text-xs font-semibold">{{ f.tipo_operacion }}</span></td>
                  <td class="px-4 py-3 text-sm text-gray-700 truncate max-w-xs">{{ f.tipo_operacion === 'Venta' ? f.receptor_nombre : f.emisor_nombre }}</td>
                  <td class="px-4 py-3 text-sm">
                    <span v-if="f.estado === 'Anulada'" class="px-2 py-1 rounded text-xs font-bold bg-red-100 text-red-700 border border-red-200">ANULADA</span>
                    <span v-else :class="f.es_exportacion ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-700'" class="px-2 py-1 rounded text-xs font-semibold">{{ f.es_exportacion ? 'Exportación' : 'Local' }}</span>
                  </td>
                  <td class="px-4 py-3 text-sm font-mono text-right">{{ formatCurrency(f.total_iva, f.moneda) }}</td>
                  <td class="px-4 py-3 text-sm font-mono text-gray-600">{{ formatTipoCambio(f.tipo_cambio, f.moneda) }}</td>
                  <td class="px-4 py-3 text-sm font-bold text-gray-700">{{ f.moneda }}</td>
                  <td class="px-4 py-3 text-sm font-bold text-right text-blue-700">
                    {{ f.tipo_operacion === 'Compra' ? formatCurrency(f.total, f.moneda) : '-' }}
                  </td>
                  <td class="px-4 py-3 text-sm font-bold text-right text-green-700">
                    {{ f.tipo_operacion === 'Venta' ? formatCurrency(f.total, f.moneda) : '-' }}
                  </td>
                  <td class="px-4 py-3 text-sm">
                    <div v-if="f.validado" class="flex flex-col items-start gap-1">
                      <span class="px-2 py-1 rounded text-xs font-bold bg-green-100 text-green-700 border border-green-200">✅ Validada</span>
                      <span v-if="f.fecha_validacion" class="text-[10px] text-gray-500">{{ formFechaValidacion(f.fecha_validacion) }}</span>
                    </div>
                    <span v-else class="px-2 py-1 rounded text-xs font-bold bg-gray-100 text-gray-600 border border-gray-200">❌ Pendiente</span>
                  </td>
                </tr>
                <tr v-if="sortedFacturas.length === 0">
                  <td colspan="12" class="px-4 py-8 text-center text-gray-500">No se encontraron facturas para esta empresa.</td>
                </tr>
              </tbody>
              <!-- 🆕 FOOTER CON TOTALES -->
              <tfoot v-if="facturasFiltradas.length > 0" class="bg-gray-100 font-semibold">
                <tr>
                  <td colspan="9" class="px-4 py-3 text-right text-sm text-gray-700">TOTALES DEL PERÍODO:</td>
                  <td class="px-4 py-3 text-right text-sm font-mono text-blue-700">
                    {{ formatCurrency(totalesCompras, 'GTQ') }}
                  </td>
                  <td class="px-4 py-3 text-right text-sm font-mono text-green-700">
                    {{ formatCurrency(totalesVentas, 'GTQ') }}
                  </td>
                  <td></td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      </div>

      <!-- Modal XLS -->
      <div v-if="resultadoXLS" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div class="bg-white rounded-lg shadow-xl max-w-lg w-full p-6">
          <h3 class="text-lg font-bold mb-2" :class="resultadoXLS.success ? 'text-green-600' : 'text-red-600'">{{ resultadoXLS.success ? '✅ Validación Exitosa' : '⚠️ Validación Rechazada' }}</h3>
          <p class="text-gray-600 mb-4">{{ resultadoXLS.mensaje }}</p>
          <ul v-if="resultadoXLS.pendientes?.length" class="bg-gray-50 p-3 rounded text-sm font-mono text-red-700 max-h-40 overflow-y-auto mb-4">
            <li v-for="p in resultadoXLS.pendientes" :key="p">• {{ p }}</li>
          </ul>
          <button @click="resultadoXLS = null" class="w-full bg-gray-200 hover:bg-gray-300 text-gray-800 py-2 rounded font-medium">Cerrar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useCompanyStore } from '@/stores/company'
import api from '@/services/api'
import { formatDateGT, formatDateTimeGT } from '@/utils/dates'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const companyStore = useCompanyStore()

const facturas = ref([])
const loading = ref(false)
const uploading = ref(false)
const statusMsg = ref('')
const statusType = ref('success')
const fileXML = ref(null)
const fileXLS = ref(null)
const validando = ref(false)
const resultadoXLS = ref(null)
const sortConfig = ref({ field: 'fecha_emision', direction: 'desc' })

// 🆕 Filtros de período
const filtroMes = ref('')
const filtroAnio = ref('')

const meses = [
  { value: '1', label: 'Enero' },
  { value: '2', label: 'Febrero' },
  { value: '3', label: 'Marzo' },
  { value: '4', label: 'Abril' },
  { value: '5', label: 'Mayo' },
  { value: '6', label: 'Junio' },
  { value: '7', label: 'Julio' },
  { value: '8', label: 'Agosto' },
  { value: '9', label: 'Septiembre' },
  { value: '10', label: 'Octubre' },
  { value: '11', label: 'Noviembre' },
  { value: '12', label: 'Diciembre' }
]

const anios = computed(() => {
  const aniosUnicos = [...new Set(facturas.value.map(f => new Date(f.fecha_emision).getFullYear()))]
  return aniosUnicos.sort((a, b) => b - a)
})

// 🆕 Facturas filtradas por período
const facturasFiltradas = computed(() => {
  let filtradas = [...facturas.value]
  
  if (filtroAnio.value) {
    filtradas = filtradas.filter(f => new Date(f.fecha_emision).getFullYear() === parseInt(filtroAnio.value))
  }
  
  if (filtroMes.value) {
    filtradas = filtradas.filter(f => (new Date(f.fecha_emision).getMonth() + 1) === parseInt(filtroMes.value))
  }
  
  return filtradas
})

// 🆕 Totales calculados (corregidos para manejar strings y usar total_gtq)
const totalesCompras = computed(() => {
  return facturasFiltradas.value
    .filter(f => f.tipo_operacion === 'Compra')
    .reduce((sum, f) => {
      // Usar total_gtq si existe (ya convertido), sino convertir total
      const monto = f.total_gtq ? parseFloat(f.total_gtq) : parseFloat(f.total) || 0
      return sum + monto
    }, 0)
})

const totalesVentas = computed(() => {
  return facturasFiltradas.value
    .filter(f => f.tipo_operacion === 'Venta')
    .reduce((sum, f) => {
      // Usar total_gtq si existe (ya convertido con tipo de cambio), sino convertir total
      const monto = f.total_gtq ? parseFloat(f.total_gtq) : parseFloat(f.total) || 0
      return sum + monto
    }, 0)
})

const aplicarFiltros = () => {
  // Los filtros se aplican automáticamente por el computed
}

const limpiarFiltros = () => {
  filtroMes.value = ''
  filtroAnio.value = ''
}

// 🔹 Tenants para superadmin
const tenants = ref([])
const selectedTenantId = ref('')

const fetchTenants = async () => {
  if (!authStore.isSuperAdmin) return
  try {
    const res = await api.get('/tenants/')
    tenants.value = res.data.filter(t => !['sistema', 'system', 'public'].includes(t.schema_name))
  } catch (err) {
    console.error('Error cargando tenants:', err)
  }
}

const handleTenantChange = () => {
  facturas.value = []
  cargarFacturas()
}

const formatDate = (dateStr) => dateStr ? new Date(dateStr).toLocaleDateString('es-GT', { year: 'numeric', month: 'short', day: '2-digit' }) : '-'

const formatTipoCambio = (tc, moneda) => moneda === 'GTQ' ? '1.00000' : (tc ? Number(tc).toFixed(5) : 'N/A')

const formatCurrency = (amount, moneda) => {
  if (!amount || isNaN(amount)) return '0.00'  // ✅ Agregar validación NaN
  const symbol = moneda === 'GTQ' ? 'Q' : (moneda === 'USD' ? '$' : moneda)
  return `${symbol} ${Number(amount).toLocaleString('es-GT', { minimumFractionDigits: 2 })}`
}

const getTipoDTEClass = (codigo) => {
  const map = { FACT: 'bg-blue-100 text-blue-700', FCAM: 'bg-indigo-100 text-indigo-700', NCRE: 'bg-orange-100 text-orange-700', NDEB: 'bg-red-100 text-red-700', CIVA: 'bg-teal-100 text-teal-700', FESP: 'bg-pink-100 text-pink-700' }
  return `px-2 py-1 rounded text-xs font-semibold ${map[codigo] || 'bg-gray-100 text-gray-700'}`
}

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
  const sorted = [...facturasFiltradas.value]
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

const formFechaValidacion = (d) => d ? new Date(d).toLocaleString('es-GT', { dateStyle: 'short', timeStyle: 'short' }) : ''

const cargarFacturas = async () => {
  if (!companyStore.selectedCompanyId) {
    facturas.value = []
    return
  }
  loading.value = true
  try {
    const params = {}
    if (authStore.isSuperAdmin && selectedTenantId.value) {
      params.tenant_id = selectedTenantId.value
    }
    const { data } = await api.get('/facturas/', { params })
    facturas.value = data
  } catch (err) {
    console.error('Error cargando facturas:', err)
  } finally {
    loading.value = false
  }
}

const handleFileSelect = async (event) => {
  const files = Array.from(event.target.files).filter(f => {
    const ext = f.name.toLowerCase().split('.').pop()
    return ext === 'xml' || ext === 'pdf'
  })
  if (!files.length) {
    statusMsg.value = '⚠️ Solo se permiten archivos XML o PDF'
    statusType.value = 'error'
    event.target.value = ''
    return
  }
  if (!companyStore.selectedCompanyId) {
    statusMsg.value = '⚠️ Selecciona una empresa antes de cargar'
    statusType.value = 'error'
    return
  }
  await uploadFacturas(files)
  event.target.value = ''
}

const uploadFacturas = async (files) => {
  uploading.value = true; statusMsg.value = ''
  try {
    const formData = new FormData()
    files.forEach(file => formData.append('files', file))
    const params = {}
    if (authStore.isSuperAdmin && selectedTenantId.value) params.tenant_id = selectedTenantId.value
    const { data } = await api.post('/facturas/upload', formData, { params, headers: {'Content-Type': undefined} })
    const revisionManual = data.requieren_revision_manual?.length || 0
    let msg = `✅ ${data.cargadas} facturas cargadas.`
    if (revisionManual > 0) {
      msg += ` ⚠️ ${revisionManual} requieren revisión manual (PDF sin XML embebido).`
    }
    if (data.rechazadas?.length) {
      msg += ` ❌ ${data.rechazadas.length} rechazadas.`
    }
    statusMsg.value = msg; statusType.value = 'success'
    await cargarFacturas()
  } catch (err) {
    statusMsg.value = `❌ ${err.response?.data?.detail || err.message}`; statusType.value = 'error'
  } finally {
    uploading.value = false
  }
}

const validarXLS = async (e) => {
  const file = e.target.files[0]
  if (!file || !companyStore.selectedCompanyId) return
  validando.value = true; resultadoXLS.value = null
  try {
    const fd = new FormData()
    fd.append('file', file)
    const params = {}
    if (authStore.isSuperAdmin && selectedTenantId.value) params.tenant_id = selectedTenantId.value
    const { data } = await api.post('/facturas/validar-hoja-electronica', fd, { params, headers: {'Content-Type': undefined} })
    resultadoXLS.value = data
    if (data.success) await cargarFacturas()
  } catch (err) {
    resultadoXLS.value = { success: false, mensaje: err.response?.data?.detail || 'Error de conexión' }
  } finally {
    validando.value = false; e.target.value = ''
  }
}

watch(() => companyStore.selectedCompanyId, async (newId) => {
  if (newId) {
    await cargarFacturas()
  } else {
    facturas.value = []
  }
})

onMounted(async () => {
  await fetchTenants()
  if (authStore.isSuperAdmin && tenants.value.length > 0) {
    selectedTenantId.value = tenants.value[0].id
  }
  if (companyStore.selectedCompanyId) {
    await cargarFacturas()
  }
})
</script>