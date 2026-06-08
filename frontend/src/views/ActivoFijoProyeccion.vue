<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-6xl mx-auto space-y-6">
      
      <!-- Encabezado y Navegacion -->
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <button @click="regresar" class="p-2 text-gray-600 hover:bg-gray-200 rounded-full transition" title="Volver">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </button>
          <div>
            <h1 class="text-2xl font-bold text-gray-800">Proyeccion de Depreciacion</h1>
            <p class="text-sm text-gray-500">{{ store.proyeccion?.descripcion }} ({{ store.proyeccion?.codigo_interno }})</p>
          </div>
        </div>
      </div>

      <!-- Tarjetas de Resumen -->
      <div v-if="store.proyeccion" class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="bg-white p-4 rounded-lg shadow border-l-4 border-blue-500">
          <p class="text-xs font-semibold text-gray-500 uppercase">Valor Costo</p>
          <p class="text-xl font-bold text-gray-900">Q {{ formatMoney(store.proyeccion.valor_costo) }}</p>
        </div>
        <div class="bg-white p-4 rounded-lg shadow border-l-4 border-yellow-500">
          <p class="text-xs font-semibold text-gray-500 uppercase">Valor Residual</p>
          <p class="text-xl font-bold text-gray-900">Q {{ formatMoney(store.proyeccion.valor_residual) }}</p>
        </div>
        <div class="bg-white p-4 rounded-lg shadow border-l-4 border-indigo-500">
          <p class="text-xs font-semibold text-gray-500 uppercase">Base Depreciable</p>
          <p class="text-xl font-bold text-gray-900">Q {{ formatMoney(store.proyeccion.valor_costo - store.proyeccion.valor_residual) }}</p>
        </div>
        <div class="bg-white p-4 rounded-lg shadow border-l-4 border-emerald-500">
          <p class="text-xs font-semibold text-gray-500 uppercase">Valor en Libros Actual</p>
          <p class="text-xl font-bold text-gray-900">Q {{ formatMoney(valorEnLibrosActual) }}</p>
        </div>
      </div>

      <!-- Estado de Carga -->
      <div v-if="store.loading" class="bg-white rounded-lg shadow p-12 text-center text-gray-500">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mb-2"></div>
        <p>Calculando proyeccion...</p>
      </div>

      <!-- Tabla de Proyeccion -->
      <div v-else-if="store.proyeccion" class="bg-white rounded-lg shadow overflow-hidden">
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-100">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Periodo</th>
                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Depreciacion del Mes</th>
                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Depreciacion Acumulada</th>
                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Valor en Libros</th>
                <th class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Estado</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr 
                v-for="fila in store.proyeccion.proyeccion" 
                :key="`${fila.anio_periodo}-${fila.mes_periodo}`"
                :class="{
                  'bg-blue-50': esPeriodoActual(fila.anio_periodo, fila.mes_periodo),
                  'bg-gray-100 text-gray-500': fila.valor_en_libros <= store.proyeccion.valor_residual && !esPeriodoActual(fila.anio_periodo, fila.mes_periodo)
                }"
                class="hover:bg-gray-50 transition"
              >
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {{ obtenerNombreMes(fila.mes_periodo) }} {{ fila.anio_periodo }}
                  <span v-if="esPeriodoActual(fila.anio_periodo, fila.mes_periodo)" class="ml-2 px-2 py-0.5 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                    Actual
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700 text-right font-mono">Q {{ formatMoney(fila.monto_depreciacion_mes) }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700 text-right font-mono">Q {{ formatMoney(fila.depreciacion_acumulada_hasta_fecha) }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900 text-right font-mono">Q {{ formatMoney(fila.valor_en_libros) }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-center">
                  <span v-if="fila.valor_en_libros <= store.proyeccion.valor_residual" class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-200 text-gray-800">Totalmente Depreciado</span>
                </td>
                <td class="px-4 py-2 text-xs text-gray-600">
                  <span v-if="fila.nota" class="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full">
                    {{ fila.nota }}
                  </span>
                  <span v-else-if="fila.es_historico" class="text-blue-600">Histórico</span>
                  <span v-else class="text-gray-400">Proyectado</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Mensaje de Error -->
      <div v-else-if="store.error" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
        {{ store.error }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useActivosFijosStore } from '@/stores/activosFijos'

const route = useRoute()
const router = useRouter()
const store = useActivosFijosStore()

const activoId = route.params.id
const empresaId = route.query.empresa_id

const meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

const obtenerNombreMes = (mesNumero) => meses[mesNumero - 1] || 'Desconocido'

const formatMoney = (value) => {
  if (value === null || value === undefined) return '0.00'
  return Number(value).toLocaleString('es-GT', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const esPeriodoActual = (anio, mes) => {
  const hoy = new Date()
  return anio === hoy.getFullYear() && mes === (hoy.getMonth() + 1)
}

const valorEnLibrosActual = computed(() => {
  if (!store.proyeccion) return 0
  const filaActual = store.proyeccion.proyeccion.find(fila => esPeriodoActual(fila.anio_periodo, fila.mes_periodo))
  return filaActual ? filaActual.valor_en_libros : store.proyeccion.valor_costo
})

const regresar = () => {
  const empresaId = route.query.empresa_id
  router.push({ 
    path: '/dashboard/activos-fijos',
    query: { empresa_id: empresaId } 
  })
}

onMounted(() => {
  if (activoId && empresaId) {
    store.fetchProyeccion(activoId, empresaId)
  }
})
</script>