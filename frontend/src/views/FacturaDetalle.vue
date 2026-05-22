<template>
  <div>
    <div class="flex items-center gap-4 mb-6">
      <button @click="volver" class="text-blue-500 hover:text-blue-700">
        ← Volver a Facturas
      </button>
      <h2 class="text-2xl font-bold">Detalle de Factura Electrónica</h2>
    </div>

    <div v-if="cargando" class="text-center py-8 text-gray-500">Cargando...</div>
    <div v-else-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">{{ error }}</div>
    <div v-else-if="factura" class="space-y-4">
      <!-- Encabezado de la factura -->
      <div class="bg-white shadow-md rounded-lg p-6">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <span class="text-sm text-gray-500">Autorización</span>
            <p class="font-semibold">{{ factura.numero_autorizacion }}</p>
          </div>
          <div>
            <span class="text-sm text-gray-500">Número</span>
            <p class="font-semibold">{{ factura.serie }} {{ factura.numero }}</p>
          </div>
          <div>
            <span class="text-sm text-gray-500">Fecha</span>
            <p class="font-semibold">{{ formatearFecha(factura.fecha_emision) }}</p>
          </div>
          <div>
            <span class="text-sm text-gray-500">Moneda</span>
            <p class="font-semibold">{{ factura.moneda }}</p>
          </div>
          <div>
            <span class="text-sm text-gray-500">Emisor</span>
            <p class="font-semibold">{{ factura.emisor_nombre }}</p>
          </div>
          <div>
            <span class="text-sm text-gray-500">Receptor</span>
            <p class="font-semibold">{{ factura.receptor_nombre }}</p>
          </div>
          <div>
            <span class="text-sm text-gray-500">Total Gravado</span>
            <p class="font-semibold">{{ factura.moneda }} {{ factura.total_gravado }}</p>
          </div>
          <div>
            <span class="text-sm text-gray-500">Total IVA</span>
            <p class="font-semibold">{{ factura.moneda }} {{ factura.total_iva }}</p>
          </div>
          <div>
            <span class="text-sm text-gray-500">Total</span>
            <p class="font-semibold">{{ factura.moneda }} {{ factura.total }}</p>
          </div>
          <div>
            <span class="text-sm text-gray-500">Tipo</span>
            <p class="font-semibold">{{ factura.es_exportacion ? 'Factura de Exportación' : 'Factura Local' }}</p>
          </div>
        </div>
      </div>

      <!-- Líneas de detalle -->
      <div class="bg-white shadow-md rounded-lg overflow-hidden">
        <div class="p-4 border-b border-gray-200">
          <h3 class="font-semibold text-gray-700">Líneas de Detalle</h3>
        </div>
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Descripción</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Cantidad</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Precio Unit.</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">IVA</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total Línea</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="item in detalles" :key="item.id">
              <td class="px-4 py-3 text-sm">{{ item.descripcion }}</td>
              <td class="px-4 py-3 text-sm text-right">{{ item.cantidad }}</td>
              <td class="px-4 py-3 text-sm text-right">{{ item.precio_unitario }}</td>
              <td class="px-4 py-3 text-sm text-right">{{ item.iva_linea }}</td>
              <td class="px-4 py-3 text-sm text-right">{{ item.total_linea }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'

const route = useRoute()
const router = useRouter()
const factura = ref(null)
const detalles = ref([])
const cargando = ref(true)
const error = ref('')

function formatearFecha(fecha) {
  if (!fecha) return ''
  return fecha.includes('T') ? fecha.split('T')[0] : fecha.substring(0, 10)
}

function volver() {
  router.push({ path: '/dashboard/facturas', query: route.query })
}

async function cargarFactura() {
  try {
    // Asumimos que el endpoint GET /facturas/{id} devuelve el detalle, si no, podríamos hacer una solicitud adicional
    const resp = await api.get(`/facturas/${route.params.id}`)
    factura.value = resp.data
    // Si el endpoint no devuelve detalles, necesitamos un endpoint adicional. Por ahora, asumimos que sí.
    detalles.value = resp.data.detalles || []
  } catch (err) {
    error.value = 'Error al cargar la factura'
  } finally {
    cargando.value = false
  }
}

onMounted(cargarFactura)
</script>