<!-- src/views/Reportes.vue -->
<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-6xl mx-auto space-y-6">
      <h2 class="text-2xl font-bold text-gray-800">Reportes Financieros</h2>

      <!-- Mensaje de error -->
      <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        {{ error }}
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

      <!-- Selector de empresa y fechas -->
      <!-- ✅ MENSAJE SI NO HAY EMPRESA SELECCIONADA -->
      <div v-if="!companyStore.selectedCompanyId" class="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-12 rounded-lg text-center">
        <svg class="w-12 h-12 mx-auto mb-3 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
        <p class="text-lg font-semibold">Selecciona una empresa desde la barra superior para generar reportes</p>
      </div>

      <!-- ✅ Panel de fechas (solo si hay empresa seleccionada) -->
      <div v-else class="bg-white shadow-md rounded-lg p-4">
        <div class="flex items-center gap-4 mb-4 pb-4 border-b border-gray-200">
          <div class="flex items-center gap-2">
            <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            <span class="text-sm text-gray-600">Empresa:</span>
            <span class="font-semibold text-gray-800">{{ empresaNombre }}</span>
          </div>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div v-if="tipoReporte !== 'balance-general'">
            <label class="block text-gray-700 text-sm font-bold mb-2">Fecha Inicio</label>
            <DateInput
              v-model="fechaInicio"
              placeholder="dd/mm/yyyy"
            />
          </div>
          <div v-if="tipoReporte !== 'balance-general'">
            <label class="block text-gray-700 text-sm font-bold mb-2">Fecha Fin</label>
            <DateInput
              v-model="fechaFin"
              placeholder="dd/mm/yyyy"
            />
          </div>
          <div v-else>
            <label class="block text-gray-700 text-sm font-bold mb-2">Fecha de Corte</label>
            <DateInput
              v-model="fechaCorte"
              placeholder="dd/mm/yyyy"
            />
          </div>
        </div>
      </div>

      <!-- Pestañas de tipo de reporte -->
      <div class="bg-white shadow-md rounded-lg overflow-hidden">
        <div class="flex border-b border-gray-200">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="cambiarTipo(tab.id)"
            :class="[
              'px-6 py-3 text-sm font-medium',
              tipoReporte === tab.id
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            ]"
          >
            {{ tab.nombre }}
          </button>
        </div>
      </div>

      <!-- Botones de acción -->
      <div class="flex gap-3">
      <button
        @click="generarReporte()"
        :disabled="!companyStore.selectedCompanyId || cargando"
        class="bg-blue-500 text-white px-6 py-2 rounded-md hover:bg-blue-600 transition disabled:opacity-50"
      >
        {{ cargando ? 'Generando...' : 'Generar Reporte' }}
      </button>
      <button
        @click="generarReporte('excel')"
        :disabled="!companyStore.selectedCompanyId || cargando"
        class="bg-green-500 text-white px-4 py-2 rounded-md hover:bg-green-600 transition disabled:opacity-50"
      >
        <span v-if="cargando">Generando...</span>
        <span v-else> Excel</span>
      </button>
      <button
        @click="generarReporte('pdf')"
        :disabled="!companyStore.selectedCompanyId || cargando"
        class="bg-red-500 text-white px-4 py-2 rounded-md hover:bg-red-600 transition disabled:opacity-50"
      >
        <span v-if="cargando">Generando...</span>
        <span v-else>📄 PDF</span>
      </button>
      </div>

      <!-- Estado de carga -->
      <div v-if="cargando" class="text-center py-8 text-gray-500">Cargando...</div>

      <!-- Balance de Comprobación -->
      <div v-if="!cargando && tipoReporte === 'balance-comprobacion' && balanceComp" class="bg-white shadow-md rounded-lg overflow-hidden">
        <h3 class="p-4 font-semibold text-gray-700 border-b">Balance de Comprobación</h3>
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Código</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cuenta</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Debe</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Haber</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Saldo</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="fila in balanceComp.filas" :key="fila.cuenta_id" class="hover:bg-gray-50">
              <td class="px-4 py-3 whitespace-nowrap text-sm font-mono text-blue-600 hover:text-blue-800">
                <router-link :to="`/dashboard/reportes/libro-mayor/${fila.cuenta_id}?fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}`">
                  {{ fila.codigo }}
                </router-link>
              </td>
              <td class="px-4 py-3 whitespace-nowrap text-sm">{{ fila.nombre }}</td>
              <td class="px-4 py-3 whitespace-nowrap text-sm text-right">{{ fila.sum_debe }}</td>
              <td class="px-4 py-3 whitespace-nowrap text-sm text-right">{{ fila.sum_haber }}</td>
              <td class="px-4 py-3 whitespace-nowrap text-sm text-right">{{ fila.saldo }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Estado de Resultados -->
      <div v-if="!cargando && tipoReporte === 'estado-resultados' && estadoResultados" class="space-y-4">
        <div class="bg-white shadow-md rounded-lg overflow-hidden">
          <h3 class="p-4 font-semibold text-gray-700 border-b">Ingresos</h3>
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Código</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cuenta</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Monto</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="fila in estadoResultados.ingresos" :key="fila.cuenta_id" class="hover:bg-gray-50">
                <td class="px-4 py-3 whitespace-nowrap text-sm font-mono">{{ fila.codigo }}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm">{{ fila.nombre }}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-right">{{ fila.saldo }}</td>
              </tr>
            </tbody>
            <tfoot class="bg-gray-50 font-semibold">
              <tr>
                <td colspan="2" class="px-4 py-3 text-sm text-right">Total Ingresos</td>
                <td class="px-4 py-3 text-sm text-right">{{ estadoResultados.total_ingresos }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
        <div class="bg-white shadow-md rounded-lg overflow-hidden">
          <h3 class="p-4 font-semibold text-gray-700 border-b">Gastos</h3>
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Código</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cuenta</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Monto</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="fila in estadoResultados.gastos" :key="fila.cuenta_id" class="hover:bg-gray-50">
                <td class="px-4 py-3 whitespace-nowrap text-sm font-mono">{{ fila.codigo }}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm">{{ fila.nombre }}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-right">{{ fila.saldo }}</td>
              </tr>
            </tbody>
            <tfoot class="bg-gray-50 font-semibold">
              <tr>
                <td colspan="2" class="px-4 py-3 text-sm text-right">Total Gastos</td>
                <td class="px-4 py-3 text-sm text-right">{{ estadoResultados.total_gastos }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
        <div class="bg-white shadow-md rounded-lg p-4 text-right text-lg font-bold">
          Utilidad Neta: {{ estadoResultados.utilidad_neta }}
        </div>
      </div>

      <!-- Balance General -->
      <div v-if="!cargando && tipoReporte === 'balance-general' && balanceGeneral" class="space-y-4">
        <div v-for="seccion in ['activos', 'pasivos', 'patrimonio']" :key="seccion" class="bg-white shadow-md rounded-lg overflow-hidden">
          <h3 class="p-4 font-semibold text-gray-700 border-b capitalize">{{ seccion }}</h3>
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Código</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cuenta</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Saldo</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="fila in balanceGeneral[seccion]" :key="fila.cuenta_id" class="hover:bg-gray-50">
                <td class="px-4 py-3 whitespace-nowrap text-sm font-mono">{{ fila.codigo }}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm">{{ fila.nombre }}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-right">{{ fila.saldo }}</td>
              </tr>
            </tbody>
            <tfoot class="bg-gray-50 font-semibold">
              <tr>
                <td colspan="2" class="px-4 py-3 text-sm text-right">Total {{ seccion }}</td>
                <td class="px-4 py-3 text-sm text-right">{{ balanceGeneral[`total_${seccion}`] }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
        <div class="bg-white shadow-md rounded-lg p-4 text-right text-lg font-bold">
          Utilidad del Ejercicio: {{ balanceGeneral.utilidad_ejercicio }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useCompanyStore } from '@/stores/company'  // ✅ NUEVO
import DateInput from '@/components/DateInput.vue'

const authStore = useAuthStore()
const companyStore = useCompanyStore()  // ✅ NUEVO

const tabs = [
  { id: 'balance-comprobacion', nombre: 'Balance de Comprobación' },
  { id: 'estado-resultados', nombre: 'Estado de Resultados' },
  { id: 'balance-general', nombre: 'Balance General' }
]

const tenants = ref([])
const selectedTenantId = ref('')
const tipoReporte = ref('balance-comprobacion')
const fechaInicio = ref('')
const fechaFin = ref('')
const fechaCorte = ref('')
const cargando = ref(false)
const error = ref('')
const balanceComp = ref(null)
const estadoResultados = ref(null)
const balanceGeneral = ref(null)

// ✅ Computed: usar empresa del contexto global
const empresaId = computed(() => companyStore.selectedCompanyId)
const empresaNombre = computed(() => companyStore.currentCompany?.nombre || '')

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

const handleTenantChange = () => {
  balanceComp.value = null
  estadoResultados.value = null
  balanceGeneral.value = null
  error.value = ''
}

function cambiarTipo(id) {
  tipoReporte.value = id
  balanceComp.value = null
  estadoResultados.value = null
  balanceGeneral.value = null
  error.value = ''
}

async function descargarArchivo(url) {
  try {
    const response = await fetch(url, {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Error al descargar' }))
      throw new Error(err.detail || 'Error al descargar')
    }
    const blob = await response.blob()
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    const disposition = response.headers.get('Content-Disposition')
    let filename = 'reporte'
    if (disposition && disposition.includes('filename=')) {
      filename = disposition.split('filename=')[1].replace(/"/g, '')
    } else {
      if (url.endsWith('.xlsx')) filename += '.xlsx'
      else if (url.endsWith('.pdf')) filename += '.pdf'
    }
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(link.href)
  } catch (err) {
    error.value = err.message
  }
}

const PATH_MAP = {
  'balance-comprobacion': 'comprobacion',
  'estado-resultados': 'estado-resultados',
  'balance-general': 'balance-general'
}

async function generarReporte(formato = null) {
  if (!empresaId.value) return
  cargando.value = true
  error.value = ''
  const segmento = PATH_MAP[tipoReporte.value]
  const basePath = `/balances/${segmento}`
  const params = { empresa_id: empresaId.value }
  
  //  Agregar tenant_id si es superadmin
  if (authStore.isSuperAdmin && selectedTenantId.value) {
    params.tenant_id = selectedTenantId.value
  }
  
  if (tipoReporte.value === 'balance-general') {
    if (!fechaCorte.value) {
      error.value = 'Debe seleccionar la fecha de corte'
      cargando.value = false
      return
    }
    params.fecha = fechaCorte.value
  } else {
    if (!fechaInicio.value || !fechaFin.value) {
      error.value = 'Debe seleccionar fecha inicio y fin'
      cargando.value = false
      return
    }
    params.fecha_inicio = fechaInicio.value
    params.fecha_fin = fechaFin.value
  }
  
  try {
    if (formato) {
      const url = `/api/v1/balances/${segmento}/${formato}?${new URLSearchParams(params).toString()}`
      await descargarArchivo(url)
    } else {
      const resp = await api.get(basePath, { params })
      const data = resp.data
      if (tipoReporte.value === 'balance-comprobacion') balanceComp.value = data
      else if (tipoReporte.value === 'estado-resultados') estadoResultados.value = data
      else if (tipoReporte.value === 'balance-general') balanceGeneral.value = data
    }
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || 'Error al generar el reporte'
  } finally {
    cargando.value = false
  }
}

// ✅ Watch: Recargar cuando cambie el contexto de empresa
watch(() => companyStore.selectedCompanyId, () => {
  // Limpiar reportes al cambiar de empresa
  balanceComp.value = null
  estadoResultados.value = null
  balanceGeneral.value = null
  error.value = ''
})

onMounted(async () => {
  await fetchTenants()
  if (authStore.isSuperAdmin && tenants.value.length > 0) {
    selectedTenantId.value = tenants.value[0].id
  }
})
</script>