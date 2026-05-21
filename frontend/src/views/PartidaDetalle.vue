<template>
  <div>
    <div class="flex items-center gap-4 mb-6">
      <button @click="$router.push('/dashboard/partidas')" class="text-blue-500 hover:text-blue-700">
        ← Volver a Partidas
      </button>
      <h2 class="text-2xl font-bold">Detalle de Partida</h2>
    </div>

    <div v-if="cargando" class="text-center py-8 text-gray-500">Cargando...</div>
    <div v-else-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">{{ error }}</div>
    <div v-else-if="partida" class="space-y-4">
      <!-- Datos generales -->
      <div class="bg-white shadow-md rounded-lg p-6">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <span class="text-sm text-gray-500">Póliza</span>
            <p class="font-semibold">{{ partida.numero_poliza || 'S/N' }}</p>
          </div>
          <div>
            <span class="text-sm text-gray-500">Fecha</span>
            <p class="font-semibold">{{ partida.fecha }}</p>
          </div>
          <div>
            <span class="text-sm text-gray-500">Empresa</span>
            <p class="font-semibold">{{ partida.empresa_nombre || '-' }}</p>
          </div>
          <div>
            <span class="text-sm text-gray-500">Descripción</span>
            <p class="font-semibold">{{ partida.descripcion }}</p>
          </div>
        </div>
      </div>

      <!-- Líneas de detalle -->
      <div class="bg-white shadow-md rounded-lg overflow-hidden">
        <div class="p-4 border-b border-gray-200">
          <h3 class="font-semibold text-gray-700">Líneas de detalle</h3>
        </div>
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th @click="toggleOrder('cuenta_codigo')"
                  class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer select-none hover:bg-gray-100">
                Cuenta {{ sortIcon('cuenta_codigo') }}
              </th>
              <th @click="toggleOrder('cuenta_nombre')"
                  class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer select-none hover:bg-gray-100">
                Nombre {{ sortIcon('cuenta_nombre') }}
              </th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Debe</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Haber</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="d in detallesOrdenados" :key="d.id" class="hover:bg-gray-50">
              <td class="px-4 py-3 whitespace-nowrap text-sm font-mono text-gray-900">{{ d.cuenta_codigo }}</td>
              <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">{{ d.cuenta_nombre }}</td>
              <td class="px-4 py-3 whitespace-nowrap text-sm text-right text-blue-600">
                {{ d.tipo_movimiento === 'debe' ? d.monto : '' }}
              </td>
              <td class="px-4 py-3 whitespace-nowrap text-sm text-right text-red-600">
                {{ d.tipo_movimiento === 'haber' ? d.monto : '' }}
              </td>
            </tr>
          </tbody>
          <tfoot class="bg-gray-50 font-semibold">
            <tr>
              <td colspan="2" class="px-4 py-3 text-sm text-right">Totales</td>
              <td class="px-4 py-3 text-sm text-right text-blue-600">{{ totalDebe }}</td>
              <td class="px-4 py-3 text-sm text-right text-red-600">{{ totalHaber }}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/services/api'

const route = useRoute()
const partida = ref(null)
const cargando = ref(true)
const error = ref('')
const orderField = ref('cuenta_codigo')
const orderDir = ref('asc')

const totalDebe = computed(() => {
  if (!partida.value) return '0.00'
  return partida.value.detalles
    .filter(d => d.tipo_movimiento === 'debe')
    .reduce((sum, d) => sum + parseFloat(d.monto), 0)
    .toFixed(2)
})

const totalHaber = computed(() => {
  if (!partida.value) return '0.00'
  return partida.value.detalles
    .filter(d => d.tipo_movimiento === 'haber')
    .reduce((sum, d) => sum + parseFloat(d.monto), 0)
    .toFixed(2)
})

const detallesOrdenados = computed(() => {
  if (!partida.value) return []
  return [...partida.value.detalles].sort((a, b) => {
    let valA = a[orderField.value] || ''
    let valB = b[orderField.value] || ''
    return orderDir.value === 'asc'
      ? String(valA).localeCompare(String(valB))
      : String(valB).localeCompare(String(valA))
  })
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

async function cargarPartida() {
  cargando.value = true
  error.value = ''
  try {
    const response = await api.get(`/partidas/${route.params.id}`)
    partida.value = response.data
  } catch (err) {
    error.value = 'Error al cargar la partida'
  } finally {
    cargando.value = false
  }
}

onMounted(cargarPartida)
</script>