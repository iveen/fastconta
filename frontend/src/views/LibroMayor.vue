<template>
  <div>
    <div class="flex items-center gap-4 mb-6">
      <button @click="volver" class="text-blue-500 hover:text-blue-700">
        ← Volver a Reportes
      </button>
      <h2 class="text-2xl font-bold">Libro Mayor</h2>
    </div>

    <!-- Información de la cuenta -->
    <div class="bg-white shadow-md rounded-lg p-6 mb-4">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <span class="text-sm text-gray-500">Cuenta</span>
          <p class="font-semibold">{{ datos?.cuenta_codigo }} - {{ datos?.cuenta_nombre }}</p>
        </div>
        <div>
          <span class="text-sm text-gray-500">Naturaleza</span>
          <p class="font-semibold capitalize">{{ datos?.naturaleza }}</p>
        </div>
        <div>
          <span class="text-sm text-gray-500">Período</span>
          <p class="font-semibold">{{ $route.query.fecha_inicio }} → {{ $route.query.fecha_fin }}</p>
        </div>
        <div>
          <span class="text-sm text-gray-500">Saldo Actual</span>
          <p class="font-semibold" :class="saldoClass">{{ datos?.saldo_actual }}</p>
        </div>
      </div>
    </div>

    <!-- Mensajes -->
    <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">{{ error }}</div>
    <div v-if="cargando" class="text-center py-8 text-gray-500">Cargando movimientos...</div>

    <!-- Tabla de movimientos -->
    <div v-if="!cargando && datos" class="bg-white shadow-md rounded-lg overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Póliza</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fecha</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Descripción</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Debe</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Haber</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="mov in datos.movimientos" :key="mov.partida_id" class="hover:bg-gray-50">
            <td class="px-4 py-3 whitespace-nowrap text-sm font-mono text-blue-600 hover:text-blue-800">
            <router-link :to="`/dashboard/partidas/${mov.partida_id}`">
                {{ mov.numero_poliza || mov.partida_id.substring(0, 8) + '...' }}
            </router-link>
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">{{ mov.fecha }}</td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">{{ mov.descripcion_partida }}</td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-right text-blue-600">
              {{ mov.tipo_movimiento === 'debe' ? mov.monto : '' }}
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-right text-red-600">
              {{ mov.tipo_movimiento === 'haber' ? mov.monto : '' }}
            </td>
          </tr>
        </tbody>
        <tfoot class="bg-gray-50 font-semibold">
          <tr>
            <td colspan="3" class="px-4 py-3 text-sm text-right">Totales</td>
            <td class="px-4 py-3 text-sm text-right text-blue-600">{{ totalDebe }}</td>
            <td class="px-4 py-3 text-sm text-right text-red-600">{{ totalHaber }}</td>
          </tr>
        </tfoot>
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
const datos = ref(null)
const cargando = ref(true)
const error = ref('')

const totalDebe = computed(() => {
  if (!datos.value) return '0.00'
  return datos.value.movimientos
    .filter(m => m.tipo_movimiento === 'debe')
    .reduce((sum, m) => sum + parseFloat(m.monto), 0)
    .toFixed(2)
})

const totalHaber = computed(() => {
  if (!datos.value) return '0.00'
  return datos.value.movimientos
    .filter(m => m.tipo_movimiento === 'haber')
    .reduce((sum, m) => sum + parseFloat(m.monto), 0)
    .toFixed(2)
})

const saldoClass = computed(() => {
  if (!datos.value) return ''
  const saldo = parseFloat(datos.value.saldo_actual)
  return saldo >= 0 ? 'text-green-600' : 'text-red-600'
})

function volver() {
  router.back()
}

async function cargarMovimientos() {
  const cuentaId = route.params.cuenta_id
  const { fecha_inicio, fecha_fin } = route.query
  try {
    const resp = await api.get(`/plan-cuentas/${cuentaId}/movimientos`, {
      params: { fecha_inicio, fecha_fin }
    })
    datos.value = resp.data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al cargar movimientos'
  } finally {
    cargando.value = false
  }
}

onMounted(cargarMovimientos)
</script>