<template>
  <div>
    <h2 class="text-2xl font-bold mb-4">Reportes Financieros</h2>

    <!-- Mensaje de error -->
    <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
      {{ error }}
    </div>

    <!-- Selector de empresa -->
    <div class="bg-white shadow-md rounded-lg p-4 mb-4">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label class="block text-gray-700 text-sm font-bold mb-2">Empresa</label>
          <select
            v-model="empresaId"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">-- Seleccionar empresa --</option>
            <option v-for="emp in empresas" :key="emp.id" :value="emp.id">
              {{ emp.nombre }}
            </option>
          </select>
        </div>
        <div v-if="tipoReporte !== 'balance-general'">
          <label class="block text-gray-700 text-sm font-bold mb-2">Fecha Inicio</label>
          <input
            v-model="fechaInicio"
            type="date"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div v-if="tipoReporte !== 'balance-general'">
          <label class="block text-gray-700 text-sm font-bold mb-2">Fecha Fin</label>
          <input
            v-model="fechaFin"
            type="date"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div v-else>
          <label class="block text-gray-700 text-sm font-bold mb-2">Fecha de Corte</label>
          <input
            v-model="fechaCorte"
            type="date"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>
    </div>

    <!-- Pestañas de tipo de reporte -->
    <div class="bg-white shadow-md rounded-lg overflow-hidden mb-4">
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

    <!-- Botón generar -->
    <button
      @click="generarReporte"
      :disabled="!empresaId || cargando"
      class="mb-4 bg-blue-500 text-white px-6 py-2 rounded-md hover:bg-blue-600 transition disabled:opacity-50"
    >
      {{ cargando ? 'Generando...' : 'Generar Reporte' }}
    </button>

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
            <td class="px-4 py-3 whitespace-nowrap text-sm font-mono">{{ fila.codigo }}</td>
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
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const tabs = [
  { id: 'balance-comprobacion', nombre: 'Balance de Comprobación' },
  { id: 'estado-resultados', nombre: 'Estado de Resultados' },
  { id: 'balance-general', nombre: 'Balance General' }
]

const empresas = ref([])
const empresaId = ref('')
const tipoReporte = ref('balance-comprobacion')
const fechaInicio = ref('')
const fechaFin = ref('')
const fechaCorte = ref('')
const cargando = ref(false)
const error = ref('')
const balanceComp = ref(null)
const estadoResultados = ref(null)
const balanceGeneral = ref(null)

async function cargarEmpresas() {
  try {
    const response = await api.get('/empresas/')
    empresas.value = response.data
  } catch (err) {
    error.value = 'Error al cargar empresas'
  }
}

function cambiarTipo(id) {
  tipoReporte.value = id
  // Limpiar resultados al cambiar de reporte
  balanceComp.value = null
  estadoResultados.value = null
  balanceGeneral.value = null
  error.value = ''
}

async function generarReporte() {
  if (!empresaId.value) return
  cargando.value = true
  error.value = ''
  try {
    switch (tipoReporte.value) {
      case 'balance-comprobacion':
        if (!fechaInicio.value || !fechaFin.value) {
          error.value = 'Debe seleccionar fecha inicio y fin'
          return
        }
        const respComp = await api.get('/balances/comprobacion', {
          params: {
            empresa_id: empresaId.value,
            fecha_inicio: fechaInicio.value,
            fecha_fin: fechaFin.value
          }
        })
        balanceComp.value = respComp.data
        break

      case 'estado-resultados':
        if (!fechaInicio.value || !fechaFin.value) {
          error.value = 'Debe seleccionar fecha inicio y fin'
          return
        }
        const respEst = await api.get('/balances/estado-resultados', {
          params: {
            empresa_id: empresaId.value,
            fecha_inicio: fechaInicio.value,
            fecha_fin: fechaFin.value
          }
        })
        estadoResultados.value = respEst.data
        break

      case 'balance-general':
        if (!fechaCorte.value) {
          error.value = 'Debe seleccionar la fecha de corte'
          return
        }
        const respBG = await api.get('/balances/balance-general', {
          params: {
            empresa_id: empresaId.value,
            fecha: fechaCorte.value
          }
        })
        balanceGeneral.value = respBG.data
        break
    }
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al generar el reporte'
  } finally {
    cargando.value = false
  }
}

onMounted(cargarEmpresas)
</script>