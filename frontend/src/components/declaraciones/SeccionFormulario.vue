<template>
  <div class="bg-white rounded-lg shadow overflow-hidden" :class="seccionBorderClass">
    <div class="bg-gray-50 px-6 py-4 border-b" :class="seccionHeaderClass">
      <div class="flex justify-between items-center">
        <div>
          <h3 class="font-bold text-gray-800">{{ titulo }}</h3>
          <p class="text-sm text-gray-600">{{ descripcion }}</p>
        </div>
        <span v-if="tipoSeccion" class="px-2 py-1 rounded text-xs font-bold uppercase" :class="tipoBadgeClass">
          {{ tipoSeccion }}
        </span>
      </div>
    </div>
    
    <div class="divide-y">
      <CasillaRow
        v-for="casilla in casillas"
        :key="casilla.casilla_codigo"
        :casilla="casilla"
        :solo-lectura="estado === 'FINALIZADO'"
        :mostrar-una-columna="esSeccionReferencia"  
        @ver-facturas="$emit('ver-facturas', casilla.casilla_codigo)"
        @ajustar="$emit('ajustar', casilla)"
      />
      
      <!-- Total de sección -->
      <div class="px-6 py-3 bg-gray-100 flex justify-between font-bold text-gray-800">
        <span>Total Sección</span>
        <div class="flex gap-8">
          <span v-if="!esSeccionReferencia">{{ formatQ(totalBase, props.tipoSeccion === 'INDICADOR') }}</span>
          <span>{{ formatQ(totalImpuesto, props.tipoSeccion === 'INDICADOR') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import CasillaRow from './CasillaRow.vue'

const props = defineProps({
  titulo: { type: String, required: true },
  descripcion: { type: String, required: true },
  casillas: { type: Array, required: true },
  estado: { type: String, required: true },
  tipoSeccion: { type: String, default: '' },
})

defineEmits(['ver-facturas', 'ajustar'])

// 🔹 Detectar si es sección de referencia (una sola columna)
const esSeccionReferencia = computed(() => {
  return props.tipoSeccion === 'REFERENCIA'
})

const totalBase = computed(() => props.casillas.reduce((s, c) => s + Number(c.base_imponible || 0), 0))
const totalImpuesto = computed(() => props.casillas.reduce((s, c) => s + Number(c.monto_impuesto || 0), 0))

const formatQ = (v, esCantidad = false) => {
  const num = Number(v || 0)
  
  // Sección 9.1 (Cantidad): Sin símbolo Q, sin decimales
  if (esCantidad) {
    return num.toLocaleString('es-GT', { 
      minimumFractionDigits: 0, 
      maximumFractionDigits: 0 
    })
  }
  
  // Otras secciones: Con Q y sin decimales
  return `Q ${num.toLocaleString('es-GT', { 
    minimumFractionDigits: 0, 
    maximumFractionDigits: 0 
  })}`
}

// Estilos según tipo
const seccionHeaderClass = computed(() => {
  switch (props.tipoSeccion) {
    case 'REFERENCIA': return 'bg-purple-50 border-purple-200'
    case 'CALCULADO': return 'bg-blue-50 border-blue-200'
    case 'INDICADOR': return 'bg-gray-50 border-gray-200'
    default: return 'bg-gray-50 border-gray-200'
  }
})

const seccionBorderClass = computed(() => {
  switch (props.tipoSeccion) {
    case 'REFERENCIA': return 'border-l-4 border-l-purple-400'
    case 'CALCULADO': return 'border-l-4 border-l-blue-400'
    case 'INDICADOR': return 'border-l-4 border-l-gray-400'
    default: return ''
  }
})

const tipoBadgeClass = computed(() => {
  switch (props.tipoSeccion) {
    case 'REFERENCIA': return 'bg-purple-100 text-purple-700'
    case 'CALCULADO': return 'bg-blue-100 text-blue-700'
    case 'INDICADOR': return 'bg-gray-100 text-gray-700'
    default: return 'bg-gray-100 text-gray-700'
  }
})
</script>