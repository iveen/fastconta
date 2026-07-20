<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="md:flex md:items-center md:justify-between mb-8">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">
          Toma de Inventario: {{ store.tomaActual?.tipo }}
        </h1>
        <p class="mt-1 text-sm text-gray-500">
          Período: {{ store.tomaActual?.anio_periodo }}/{{ String(store.tomaActual?.mes_periodo).padStart(2, '0') }} 
          | Corte: {{ store.tomaActual?.fecha_corte }}
        </p>
      </div>
      <div class="mt-4 md:mt-0 flex gap-3">
        <button 
          @click="exportar('excel')"
          :disabled="store.isLoading || store.totalItemsCount === 0"
          class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
        >
          📥 Exportar Excel
        </button>
        <button 
          v-if="store.tomaActual?.estado === 'BORRADOR'"
          @click="mostrarModalImportar = true"
          class="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
        >
          📤 Importar Archivo
        </button>
        <button 
          v-if="store.tomaActual?.estado === 'BORRADOR'"
          @click="confirmarToma"
          :disabled="store.totalItemsCount === 0"
          class="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 disabled:opacity-50"
        >
          ✅ Confirmar Toma
        </button>
      </div>
    </div>

    <!-- Resumen -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <div class="text-sm font-medium text-gray-500">Total de Items</div>
        <div class="mt-2 text-3xl font-bold text-gray-900">{{ store.totalItemsCount }}</div>
      </div>
      <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <div class="text-sm font-medium text-gray-500">Valor Total del Inventario</div>
        <div class="mt-2 text-3xl font-bold text-gray-900">Q {{ Number(store.totalValor).toLocaleString('es-GT', { minimumFractionDigits: 2 }) }}</div>
      </div>
      <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <div class="text-sm font-medium text-gray-500">Estado</div>
        <div class="mt-2">
          <span :class="estadoBadgeClass" class="px-3 py-1 rounded-full text-sm font-semibold">
            {{ store.tomaActual?.estado }}
          </span>
        </div>
      </div>
    </div>

    <!-- Tabla de Items -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-200 bg-gray-50">
        <h3 class="text-lg font-medium text-gray-900">Detalle de Productos</h3>
      </div>
      
      <div v-if="store.isLoading" class="p-12 text-center text-gray-500">
        Cargando datos...
      </div>
      
      <div v-else-if="store.items.length === 0" class="p-12 text-center text-gray-500">
        No hay items en esta toma. Usa el botón "Importar Archivo" para comenzar.
      </div>

      <div v-else class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Código</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Descripción</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Bodega</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Cantidad</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Costo Unit.</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Costo Total</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="item in store.items" :key="item.public_id" class="hover:bg-gray-50 transition-colors">
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ item.codigo || 'N/A' }}</td>
              <td class="px-6 py-4 text-sm text-gray-900">{{ item.descripcion }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ item.bodega_codigo || 'N/A' }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">{{ Number(item.cantidad).toLocaleString() }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">Q {{ Number(item.costo_unitario).toLocaleString('es-GT', { minimumFractionDigits: 2 }) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 text-right">Q {{ Number(item.costo_total).toLocaleString('es-GT', { minimumFractionDigits: 2 }) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modales -->
    <ImportarArchivoModal 
      v-if="mostrarModalImportar"
      :toma-public-id="route.params.id"
      @close="mostrarModalImportar = false"
      @importacion-iniciada="handleImportacionIniciada"
    />

    <JobProgressModal 
      v-if="store.jobActivo"
      :job="store.jobActivo"
      @cerrar="store.detenerPolling()"
      @cancelar="cancelarJob"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useInventarioStore } from '@/stores/inventarioStore'
import { inventarioService } from '@/services/inventarioService'
import ImportarArchivoModal from '@/components/inventarios/ImportarArchivoModal.vue'
import JobProgressModal from '@/components/inventarios/JobProgressModal.vue'

const route = useRoute()
const store = useInventarioStore()
const mostrarModalImportar = ref(false)

const estadoBadgeClass = computed(() => {
  const map = {
    'BORRADOR': 'bg-yellow-100 text-yellow-800',
    'CONFIRMADO': 'bg-blue-100 text-blue-800',
    'CONTABILIZADO': 'bg-green-100 text-green-800'
  }
  return map[store.tomaActual?.estado] || 'bg-gray-100 text-gray-800'
})

onMounted(async () => {
  await store.cargarToma(route.params.id)
})

onUnmounted(() => {
  store.detenerPolling() // Limpiar intervalos al salir de la vista
})

async function handleImportacionIniciada(job) {
  mostrarModalImportar.value = false
  // El store ya inicia el polling automáticamente al recibir el job
}

async function cancelarJob() {
  try {
    await inventarioService.cancelarJob(store.jobActivo.public_id)
    store.detenerPolling()
  } catch (error) {
    console.error('Error al cancelar:', error)
  }
}

async function confirmarToma() {
  if (confirm('¿Estás seguro de confirmar esta toma? Esta acción no se puede deshacer.')) {
    await store.confirmarTomaAction(route.params.id)
  }
}

async function exportar(formato) {
  try {
    const { blob, filename } = await inventarioService.exportarToma(route.params.id, formato)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Error al exportar:', error)
  }
}
</script>