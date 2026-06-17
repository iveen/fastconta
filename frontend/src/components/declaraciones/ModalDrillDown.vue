<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] flex flex-col">
      <!-- Header -->
      <div class="px-6 py-4 border-b flex justify-between items-center">
        <div>
          <h3 class="font-bold text-lg">Facturas asociadas</h3>
          <p class="text-sm text-gray-600">Casilla: {{ casillaCodigo }}</p>
        </div>
        <button @click="$emit('close')" class="text-gray-500 hover:text-gray-700">✕</button>
      </div>

      <!-- Content -->
      <div class="overflow-auto flex-1 p-6">
        <div v-if="cargando" class="text-center py-8">Cargando...</div>
        <div v-else-if="!facturas.length" class="text-center py-8 text-gray-500">
          No hay facturas asociadas a esta casilla.
        </div>
        <table v-else class="w-full text-sm">
          <thead class="bg-gray-50 sticky top-0">
            <tr>
              <th class="px-3 py-2 text-left">Documento</th>
              <th class="px-3 py-2 text-left">Fecha</th>
              <th class="px-3 py-2 text-left">Tercero</th>
              <th class="px-3 py-2 text-left">NIT</th>
              <th class="px-3 py-2 text-right">Base</th>
              <th class="px-3 py-2 text-right">Impuesto</th>
            </tr>
          </thead>
          <tbody class="divide-y">
            <tr v-for="f in facturas" :key="f.factura_id" class="hover:bg-gray-50">
              <td class="px-3 py-2 font-mono">{{ f.numero }}</td>
              <td class="px-3 py-2">{{ f.fecha_emision }}</td>
              <td class="px-3 py-2">{{ f.tercero }}</td>
              <td class="px-3 py-2 font-mono">{{ f.nit }}</td>
              <td class="px-3 py-2 text-right font-mono">{{ formatQ(f.base_asignada) }}</td>
              <td class="px-3 py-2 text-right font-mono font-semibold">{{ formatQ(f.impuesto_asignado) }}</td>
            </tr>
          </tbody>
          <tfoot class="bg-gray-100 font-bold">
            <tr>
              <td colspan="4" class="px-3 py-2">TOTALES ({{ facturas.length }} facturas)</td>
              <td class="px-3 py-2 text-right font-mono">{{ formatQ(totalBase) }}</td>
              <td class="px-3 py-2 text-right font-mono">{{ formatQ(totalImpuesto) }}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { declaracionesApi } from '@/services/declaraciones' 

const props = defineProps({
  declaracionId: { type: String, required: true },
  casillaCodigo: { type: String, required: true },
})
defineEmits(['close'])

const facturas = ref([])
const cargando = ref(true)

const totalBase = computed(() => facturas.value.reduce((s, f) => s + f.base_asignada, 0))
const totalImpuesto = computed(() => facturas.value.reduce((s, f) => s + f.impuesto_asignado, 0))

const formatQ = (v) => `Q ${Number(v || 0).toLocaleString('es-GT', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`

onMounted(async () => {
  try {
    const res = await declaracionesApi.obtenerFacturas(props.declaracionId, props.casillaCodigo)
    facturas.value = res.facturas
  } finally {
    cargando.value = false
  }
})
</script>