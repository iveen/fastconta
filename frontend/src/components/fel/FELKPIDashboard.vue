<template>
  <div class="fel-kpis-dashboard">
    <!-- Filtros -->
    <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-100 mb-6">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Fecha Inicio</label>
          <input
            v-model="fechaInicio"
            type="text"
            placeholder="dd/mm/yyyy"
            @input="formatDateInput($event, 'fechaInicio')"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Fecha Fin</label>
          <input
            v-model="fechaFin"
            type="text"
            placeholder="dd/mm/yyyy"
            @input="formatDateInput($event, 'fechaFin')"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div class="flex items-end">
          <button
            @click="cargarKPIs"
            :disabled="cargando"
            class="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
          >
            {{ cargando ? 'Cargando...' : 'Consultar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Tarjetas de KPIs -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <KPICard
        titulo="Compras (sin IVA)"
        :valor="financieros.compras_sin_iva"
        color="blue"
        icono="🛒"
      />
      <KPICard
        titulo="Ventas Locales (sin IVA)"
        :valor="financieros.ventas_locales_sin_iva"
        color="green"
        icono="💰"
      />
      <KPICard
        titulo="Exportaciones (sin IVA)"
        :valor="financieros.exportaciones_sin_iva"
        color="purple"
        icono="🌎"
      />
      <KPICard
        titulo="IVA por Pagar"
        :valor="financieros.iva_por_pagar"
        :color="financieros.iva_por_pagar >= 0 ? 'red' : 'green'"
        icono="📊"
      />
    </div>

    <!-- Segunda fila de KPIs -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <KPICard
        titulo="Crédito Fiscal"
        :valor="financieros.credito_fiscal"
        color="teal"
        icono="✅"
      />
      <KPICard
        titulo="Débito Fiscal"
        :valor="financieros.debito_fiscal"
        color="orange"
        icono="📤"
      />
      <KPICard
        titulo="Documentos Emitidos"
        :valor="conteos.emitidos"
        color="indigo"
        icono="📄"
        :es-numero="true"
      />
      <KPICard
        titulo="Documentos Recibidos"
        :valor="conteos.recibidos"
        color="pink"
        icono="📥"
        :es-numero="true"
      />
    </div>

    <!-- Tercera fila - Documentos Anulados -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <KPICard
        titulo="Documentos Anulados"
        :valor="conteos.anulados"
        color="red"
        icono="❌"
        :es-numero="true"
      />
      <KPICard
        titulo="Total Documentos"
        :valor="conteos.total"
        color="gray"
        icono="📋"
        :es-numero="true"
      />
    </div>

    <!-- Gráficos -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Gráfico de Ventas vs Compras -->
      <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <h3 class="text-lg font-semibold mb-4">Ventas vs Compras (Mensual)</h3>
        <apexchart
          v-if="chartOptionsVentasCompras"
          type="bar"
          height="350"
          :options="chartOptionsVentasCompras"
          :series="seriesVentasCompras"
        />
      </div>

      <!-- Gráfico de IVA -->
      <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <h3 class="text-lg font-semibold mb-4">Crédito vs Débito Fiscal</h3>
        <apexchart
          v-if="chartOptionsIVA"
          type="line"
          height="350"
          :options="chartOptionsIVA"
          :series="seriesIVA"
        />
      </div>

      <!-- Gráfico de Documentos -->
      <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100 lg:col-span-2">
        <h3 class="text-lg font-semibold mb-4">Documentos Emitidos vs Recibidos</h3>
        <apexchart
          v-if="chartOptionsDocumentos"
          type="area"
          height="350"
          :options="chartOptionsDocumentos"
          :series="seriesDocumentos"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import VueApexCharts from 'vue3-apexcharts'
import { toast } from 'vue3-toastify'
import KPICard from './KPICard.vue'
import { felAPI } from '@/stores/fel.js'

const apexchart = VueApexCharts

// Estado
const today = new Date()
const currentMonth = String(today.getMonth() + 1).padStart(2, '0')
const currentYear = today.getFullYear()
const firstDayOfMonth = `01/${currentMonth}/${currentYear}`
const todayFormatted = `${String(today.getDate()).padStart(2, '0')}/${currentMonth}/${currentYear}`

const fechaInicio = ref(firstDayOfMonth)
const fechaFin = ref(todayFormatted)
const cargando = ref(false)

const financieros = ref({
  compras_sin_iva: 0,
  ventas_locales_sin_iva: 0,
  exportaciones_sin_iva: 0,
  credito_fiscal: 0,
  debito_fiscal: 0,
  iva_por_pagar: 0,
})

const conteos = ref({
  emitidos: 0,
  recibidos: 0,
  anulados: 0,
  total: 0,
})

const seriesTemporales = ref([])

// Formatear fecha mientras se escribe (dd/mm/yyyy)
const formatDateInput = (event, fieldName) => {
  let value = event.target.value.replace(/\D/g, '') // Solo números
  
  if (value.length > 2) {
    value = value.slice(0, 2) + '/' + value.slice(2)
  }
  if (value.length > 5) {
    value = value.slice(0, 5) + '/' + value.slice(5, 9)
  }
  
  event.target.value = value.slice(0, 10) // dd/mm/yyyy
  
  // Actualizar el ref correspondiente
  if (fieldName === 'fechaInicio') {
    fechaInicio.value = value.slice(0, 10)
  } else if (fieldName === 'fechaFin') {
    fechaFin.value = value.slice(0, 10)
  }
}

// Convertir dd/mm/yyyy a yyyy-mm-dd para la API
const formatDateForAPI = (dateStr) => {
  if (!dateStr || dateStr.length !== 10) return null
  const [day, month, year] = dateStr.split('/')
  return `${year}-${month}-${day}`
}

// Validar fecha dd/mm/yyyy
const isValidDate = (dateStr) => {
  if (!dateStr || dateStr.length !== 10) return false
  const regex = /^\d{2}\/\d{2}\/\d{4}$/
  if (!regex.test(dateStr)) return false
  
  const [day, month, year] = dateStr.split('/').map(Number)
  const date = new Date(year, month - 1, day)
  return date.getFullYear() === year && 
         date.getMonth() === month - 1 && 
         date.getDate() === day
}

// Cargar KPIs
const cargarKPIs = async () => {
  // Validar fechas
  if (!isValidDate(fechaInicio.value)) {
    toast.error('⚠️ Fecha de inicio inválida. Use el formato dd/mm/yyyy')
    return
  }
  if (!isValidDate(fechaFin.value)) {
    toast.error('⚠️ Fecha de fin inválida. Use el formato dd/mm/yyyy')
    return
  }
  
  cargando.value = true
  try {
    const response = await felAPI.getKPIs({
      fecha_inicio: formatDateForAPI(fechaInicio.value),
      fecha_fin: formatDateForAPI(fechaFin.value),
    })
    financieros.value = response.financieros
    conteos.value = response.conteos
    seriesTemporales.value = response.series_temporales
    toast.success('✅ KPIs cargados correctamente')
  } catch (error) {
    console.error('Error cargando KPIs:', error)
    toast.error('Error al cargar KPIs: ' + (error.response?.data?.detail || error.message))
  } finally {
    cargando.value = false
  }
}

// Computadas para gráficos
const seriesVentasCompras = computed(() => [
  {
    name: 'Ventas',
    data: seriesTemporales.value.map(s => s.ventas_locales),
  },
  {
    name: 'Compras',
    data: seriesTemporales.value.map(s => s.compras),
  },
  {
    name: 'Exportaciones',
    data: seriesTemporales.value.map(s => s.exportaciones),
  },
])

const chartOptionsVentasCompras = computed(() => ({
  chart: { type: 'bar', height: 350 },
  plotOptions: { bar: { horizontal: false, columnWidth: '55%' } },
  dataLabels: { enabled: false },
  stroke: { show: true, width: 2, colors: ['transparent'] },
  xaxis: {
    categories: seriesTemporales.value.map(s => s.periodo),
  },
  yaxis: {
    title: { text: 'Monto (GTQ)' },
    labels: {
      formatter: (val) => `Q${val.toLocaleString()}`,
    },
  },
  fill: { opacity: 1 },
  tooltip: {
    y: {
      formatter: (val) => `Q${val.toLocaleString()}`,
    },
  },
  colors: ['#10B981', '#3B82F6', '#8B5CF6'],
}))

const seriesIVA = computed(() => [
  {
    name: 'Débito Fiscal',
    data: seriesTemporales.value.map(s => s.debito_fiscal),
  },
  {
    name: 'Crédito Fiscal',
    data: seriesTemporales.value.map(s => s.credito_fiscal),
  },
])

const chartOptionsIVA = computed(() => ({
  chart: { type: 'line', height: 350 },
  stroke: { curve: 'smooth', width: 3 },
  xaxis: {
    categories: seriesTemporales.value.map(s => s.periodo),
  },
  yaxis: {
    title: { text: 'IVA (GTQ)' },
    labels: {
      formatter: (val) => `Q${val.toLocaleString()}`,
    },
  },
  colors: ['#F59E0B', '#14B8A6'],
  tooltip: {
    y: {
      formatter: (val) => `Q${val.toLocaleString()}`,
    },
  },
}))

const seriesDocumentos = computed(() => [
  {
    name: 'Emitidos',
    data: seriesTemporales.value.map(s => s.documentos_emitidos),
  },
  {
    name: 'Recibidos',
    data: seriesTemporales.value.map(s => s.documentos_recibidos),
  },
  {
    name: 'Anulados',
    data: seriesTemporales.value.map(s => s.documentos_anulados),
  },
])

const chartOptionsDocumentos = computed(() => ({
  chart: { type: 'area', height: 350 },
  dataLabels: { enabled: false },
  stroke: { curve: 'smooth', width: 2 },
  xaxis: {
    categories: seriesTemporales.value.map(s => s.periodo),
  },
  yaxis: {
    title: { text: 'Cantidad de Documentos' },
  },
  colors: ['#6366F1', '#EC4899', '#EF4444'],
  fill: {
    type: 'gradient',
    gradient: {
      shadeIntensity: 1,
      opacityFrom: 0.7,
      opacityTo: 0.3,
    },
  },
  legend: {
    position: 'bottom',
  },
}))

onMounted(() => {
  cargarKPIs()
})
</script>