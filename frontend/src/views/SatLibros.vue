<!-- src/views/SatLibros.vue -->
<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-7xl mx-auto space-y-6">
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-2xl font-bold text-gray-800">Libros de IVA (SAT)</h1>
          <p class="text-sm text-gray-500">Generación y consulta de reportes impositivos mensuales</p>
        </div>
        <div v-if="libro" class="flex items-center gap-2">
          <span :class="statusBadgeClass(libro.estado)" class="px-3 py-1 rounded-full text-xs font-semibold uppercase">
            {{ libro.estado }}
          </span>
        </div>
      </div>

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

      <div class="bg-white p-4 rounded-xl shadow-xs border border-gray-100 flex flex-wrap gap-4 items-end">
        <div class="flex flex-col gap-1 w-64">
          <label class="text-xs font-semibold text-gray-600 uppercase">Empresa <span class="text-red-500">*</span></label>
          <select v-model="filters.empresa_id" @change="limpiarLibro" class="border border-gray-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none w-full">
            <option value="" disabled>-- Seleccione una empresa --</option>
            <option v-for="emp in empresas" :key="emp.id" :value="emp.id">
              {{ emp.nombre }} ({{ emp.nit }})
            </option>
          </select>
        </div>

        <div class="flex flex-col gap-1 w-40">
          <label class="text-xs font-semibold text-gray-600 uppercase">Tipo de Libro</label>
          <select v-model="filters.tipo_libro" @change="limpiarLibro" class="border border-gray-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none w-full">
            <option value="compras">📥 Compras</option>
            <option value="ventas">📤 Ventas</option>
          </select>
        </div>

        <div class="flex flex-col gap-1 w-48">
          <label class="text-xs font-semibold text-gray-600 uppercase">Régimen Fiscal</label>
          <select v-model="filters.regimen_fiscal" :disabled="libro && libro.estado === 'finalizado'" class="border border-gray-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none disabled:bg-gray-100 w-full">
            <option value="general">Régimen General</option>
            <option value="pequeno_contribuyente">Pequeño Contribuyente</option>
          </select>
        </div>

        <div class="flex flex-col gap-1 w-24">
          <label class="text-xs font-semibold text-gray-600 uppercase">Año</label>
          <input type="number" v-model.number="filters.anio" @change="limpiarLibro" min="2020" max="2100" class="border border-gray-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none w-full" />
        </div>

        <div class="flex flex-col gap-1 w-36">
          <label class="text-xs font-semibold text-gray-600 uppercase">Mes</label>
          <select v-model.number="filters.mes" @change="limpiarLibro" class="border border-gray-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none w-full">
            <option v-for="(mesNombre, index) in meses" :key="index + 1" :value="index + 1">
              {{ mesNombre }}
            </option>
          </select>
        </div>

        <button @click="consultarLibro" :disabled="!filters.empresa_id || cargando"
          class="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2 rounded-lg font-medium shadow-sm transition disabled:opacity-50 flex items-center gap-2 cursor-pointer h-[38px]">
          <span>🔍</span> Consultar
        </button>
      </div>

      <div v-if="statusMsg" :class="statusType === 'error' ? 'bg-red-50 border-red-500 text-red-700' : 'bg-green-50 border-green-500 text-green-700'" class="p-4 rounded-lg border-l-4 font-medium text-sm flex justify-between items-center shadow-xs">
        <span>{{ statusMsg }}</span>
        <button @click="statusMsg = ''" class="text-gray-400 hover:text-gray-600 font-bold text-lg">×</button>
      </div>

      <div v-if="cargando" class="flex flex-col items-center justify-center py-20">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <p class="mt-4 text-gray-500 font-medium text-sm">Procesando información de la SAT...</p>
      </div>

      <div v-else-if="libroNoExiste && filters.empresa_id" class="bg-white rounded-xl border border-dashed border-gray-300 p-12 text-center max-w-2xl mx-auto shadow-xs">
        <span class="text-4xl">📋</span>
        <h3 class="mt-4 text-lg font-bold text-gray-800">No se ha generado este libro</h3>
        <p class="mt-2 text-sm text-gray-500 max-w-md mx-auto">
          No encontramos ningún registro procesado para el periodo de <span class="font-semibold">{{ meses[filters.mes - 1] }} del {{ filters.anio }}</span>. Puede estructurarlo automáticamente con las FEL válidas del sistema.
        </p>
        <button @click="generarORecalcularLibro" :disabled="procesandoAccion"
          class="mt-6 bg-purple-600 hover:bg-purple-700 text-white px-6 py-2.5 rounded-lg font-semibold shadow-sm transition flex items-center gap-2 mx-auto cursor-pointer disabled:opacity-50">
          ✨ {{ procesandoAccion ? 'Generando...' : 'Estructurar Libro de IVA' }}
        </button>
      </div>

      <div v-else-if="libro" class="space-y-6 animate-fade-in">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div class="bg-white p-4 rounded-xl border border-gray-100 shadow-xs">
            <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Documentos</p>
            <p class="text-2xl font-bold text-gray-800 mt-1">{{ libro.total_lineas }}</p>
          </div>
          <div class="bg-white p-4 rounded-xl border border-gray-100 shadow-xs">
            <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Base Imponible</p>
            <p class="text-2xl font-bold text-gray-800 mt-1">Q {{ formatMonto(libro.total_base_imponible) }}</p>
          </div>
          <div class="bg-white p-4 rounded-xl border border-gray-100 shadow-xs">
            <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Monto IVA</p>
            <p class="text-2xl font-blue-600 font-bold mt-1 text-blue-600">Q {{ formatMonto(libro.total_iva) }}</p>
          </div>
          <div class="bg-white p-4 rounded-xl border border-gray-100 shadow-xs bg-gray-50">
            <p class="text-xs font-semibold text-gray-500 uppercase tracking-wider">Monto Total</p>
            <p class="text-2xl font-bold text-gray-900 mt-1">Q {{ formatMonto(libro.total_monto) }}</p>
          </div>
        </div>

        <div v-if="libro.estado === 'borrador'" class="flex justify-end gap-3 bg-purple-50 border border-purple-100 p-4 rounded-xl">
          <p class="text-xs text-purple-700 flex-1 self-center font-medium">
            💡 Este libro se encuentra en modo borrador. Puede recalcular si cargó nuevos XMLs o cerrarlo definitivamente.
          </p>
          <button @click="generarORecalcularLibro" :disabled="procesandoAccion"
            class="bg-white border border-purple-300 hover:bg-purple-100 text-purple-700 px-4 py-2 rounded-lg text-sm font-semibold transition cursor-pointer disabled:opacity-50">
            🔄 Recalcular Datos
          </button>
          <button @click="finalizarLibro" :disabled="procesandoAccion"
            class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm font-semibold shadow-xs transition cursor-pointer disabled:opacity-50">
            🔒 Finalizar Periodo
          </button>
        </div>

        <div class="bg-white rounded-xl shadow-xs border border-gray-100 overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="bg-gray-50 border-b border-gray-100">
                  <th class="p-3 text-xs font-semibold text-gray-500 uppercase tracking-wider text-center">No.</th>
                  <th class="p-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Fecha</th>
                  <th class="p-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Documento</th>
                  <th class="p-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">NIT</th>
                  <th class="p-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Razón Social</th>
                  <th class="p-3 text-xs font-semibold text-gray-500 uppercase tracking-wider text-right">Base Exenta</th>
                  <th class="p-3 text-xs font-semibold text-gray-500 uppercase tracking-wider text-right">Base Imponible</th>
                  <th class="p-3 text-xs font-semibold text-gray-500 uppercase tracking-wider text-right">IVA</th>
                  <th class="p-3 text-xs font-semibold text-gray-500 uppercase tracking-wider text-right">
                    {{ filters.tipo_libro === 'compras' ? 'Crédito Fiscal' : 'Débito Fiscal' }}
                  </th>
                  <th class="p-3 text-xs font-semibold text-gray-500 uppercase tracking-wider text-right">Total</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100 text-sm text-gray-700">
                <tr v-for="linea in libro.lineas" :key="linea.id" class="hover:bg-gray-50/70 transition">
                  <td class="p-3 text-center text-gray-400 font-medium">{{ linea.numero_secuencia }}</td>
                  <td class="p-3 whitespace-nowrap">{{ formatDate(linea.fecha_documento) }}</td>
                  <td class="p-3 font-mono text-xs text-gray-600">{{ linea.numero_documento }}</td>
                  <td class="p-3 font-medium text-gray-900">{{ linea.nit || 'C/F' }}</td>
                  <td class="p-3 max-w-xs truncate" :title="linea.razon_social">{{ linea.razon_social || 'Consumidor Final' }}</td>
                  <td class="p-3 text-right font-medium text-green-600">Q {{ formatMonto(linea.monto_exento) }}</td>
                  <td class="p-3 text-right">Q {{ formatMonto(linea.base_imponible) }}</td>
                  <td class="p-3 text-right text-gray-500">Q {{ formatMonto(linea.monto_iva) }}</td>
                  <td class="p-3 text-right font-medium text-blue-600">
                    Q {{ filters.tipo_libro === 'compras' ? formatMonto(linea.credito_fiscal) : formatMonto(linea.debito_fiscal) }}
                  </td>
                  <td class="p-3 text-right font-semibold text-gray-900">Q {{ formatMonto(linea.monto_total) }}</td>
                </tr>
                <tr v-if="libro.lineas.length === 0">
                  <td colspan="10" class="p-8 text-center text-gray-400">
                    No existen líneas detalladas registradas en este libro.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

const tenants = ref([])
const selectedTenantId = ref('')
const empresas = ref([])

const filters = reactive({
  empresa_id: route.query.empresa || '',
  tipo_libro: 'compras',
  regimen_fiscal: 'general',
  anio: 2025,
  mes: 5
})

const cargando = ref(false)
const procesandoAccion = ref(false)
const libroNoExiste = ref(false)
const libro = ref(null)
const statusMsg = ref('')
const statusType = ref('success')

const limpiarLibro = () => {
  libro.value = null
  libroNoExiste.value = false
  statusMsg.value = ''
}

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
    const { data } = await api.get('/empresas/', { params })
    empresas.value = data

    if (route.query.empresa) {
      filters.empresa_id = route.query.empresa
      await consultarLibro()
    }
  } catch (err) {
    console.error('Error cargando empresas en libros SAT:', err)
    statusMsg.value = '❌ No se pudieron cargar las empresas del Tenant.'
    statusType.value = 'error'
  }
}

const handleTenantChange = () => {
  filters.empresa_id = ''
  limpiarLibro()
  cargarEmpresas()
}

const consultarLibro = async () => {
  if (!filters.empresa_id) return

  cargando.value = true
  libroNoExiste.value = false
  libro.value = null
  statusMsg.value = ''

  try {
    const params = {
      empresa_id: filters.empresa_id,
      tipo_libro: filters.tipo_libro,
      anio: filters.anio,
      mes: filters.mes
    }
    if (authStore.isSuperAdmin && selectedTenantId.value) {
      params.tenant_id = selectedTenantId.value
    }
    const { data } = await api.get('/sat-libros/consultar', { params })
    libro.value = data
    filters.regimen_fiscal = data.regimen_fiscal
  } catch (err) {
    if (err.response?.status === 404) {
      libroNoExiste.value = true
    } else {
      statusMsg.value = `❌ Error al consultar: ${err.response?.data?.detail || err.message}`
      statusType.value = 'error'
    }
  } finally {
    cargando.value = false
  }
}

const generarORecalcularLibro = async () => {
  if (!filters.empresa_id) return

  procesandoAccion.value = true
  statusMsg.value = ''

  try {
    const payload = {
      empresa_id: filters.empresa_id,
      tipo_libro: filters.tipo_libro,
      regimen_fiscal: filters.regimen_fiscal,
      anio_periodo: filters.anio,
      mes_periodo: filters.mes
    }
    
    const params = {}
    if (authStore.isSuperAdmin && selectedTenantId.value) {
      params.tenant_id = selectedTenantId.value
    }

    await api.post('/sat-libros/generar', payload, { params })
    statusMsg.value = '✅ Libro de IVA generado y totalizado exitosamente.'
    statusType.value = 'success'

    await consultarLibro()
  } catch (err) {
    statusMsg.value = `❌ Error al procesar: ${err.response?.data?.detail || err.message}`
    statusType.value = 'error'
  } finally {
    procesandoAccion.value = false
  }
}

const finalizarLibro = async () => {
  if (!libro.value || !confirm('¿Está seguro de finalizar este periodo? Una vez cerrado no podrá ser recalculado.')) return

  procesandoAccion.value = true
  statusMsg.value = ''

  try {
    const params = {}
    if (authStore.isSuperAdmin && selectedTenantId.value) {
      params.tenant_id = selectedTenantId.value
    }
    
    await api.patch(`/sat-libros/${libro.value.id}/finalizar`, null, { params })
    statusMsg.value = `🔒 El periodo ${meses[filters.mes - 1]} se ha congelado con éxito.`
    statusType.value = 'success'
  
    await consultarLibro()
  } catch (err) {
    statusMsg.value = `❌ Error al finalizar: ${err.response?.data?.detail || err.message}`
    statusType.value = 'error'
  } finally {
    procesandoAccion.value = false
  }
}

watch(() => filters.empresa_id, (val) => {
  if (val) router.replace({ query: { ...route.query, empresa: val } })
  else router.replace({ query: { ...route.query, empresa: undefined } })
})

onMounted(async () => {
  await fetchTenants()
  if (authStore.isSuperAdmin && tenants.value.length > 0) {
    selectedTenantId.value = tenants.value[0].id
  }
  await cargarEmpresas()
})

const formatMonto = (valor) => {
  if (!valor) return '0.00'
  return parseFloat(valor).toLocaleString('es-GT', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const formatDate = (fechaStr) => {
  if (!fechaStr) return ''
  const [year, month, day] = fechaStr.split('-')
  return `${day}/${month}/${year}`
}

const statusBadgeClass = (estado) => {
  switch (estado) {
    case 'borrador': return 'bg-yellow-100 text-yellow-800 border border-yellow-200'
    case 'finalizado': return 'bg-purple-100 text-purple-800 border border-purple-200'
    case 'presentado': return 'bg-green-100 text-green-800 border border-green-200'
    default: return 'bg-gray-100 text-gray-800'
  }
}
</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.25s ease-out forwards;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>