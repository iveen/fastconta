<template>
  <div class="px-6 py-3 hover:bg-gray-50 flex items-center gap-4">
    <!-- Indicador de ajuste manual -->
    <div v-if="casilla.es_ajuste_manual" class="w-2 h-2 bg-yellow-500 rounded-full" :title="'Ajuste manual: ' + casilla.motivo_ajuste"></div>
    <div v-else class="w-2 h-2"></div>

    <!-- Nombre -->
    <div class="flex-1 text-sm text-gray-800">
      {{ casilla.casilla_nombre }}
      <span v-if="casilla.es_ajuste_manual" class="ml-2 text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">
        Manual
      </span>
    </div>

    <!-- 🔹 Base - Solo mostrar si NO es sección de referencia -->
    <div v-if="!esReferencia" class="w-32 text-right font-mono text-sm">
      {{ formatValue(casilla.base_imponible, false) }}
    </div>

    <!-- Impuesto/Valor -->
    <div class="w-32 text-right font-mono text-sm font-semibold" :class="isIndicator ? 'text-blue-600' : ''">
      {{ formatValue(casilla.monto_impuesto, !isIndicator) }}
    </div>

    <!-- Acciones -->
    <div class="w-20 flex gap-1 justify-end">
      <button
        v-if="!soloLectura && !isIndicator"
        @click="$emit('ajustar', casilla)"
        class="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded"
        title="Ajuste manual"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
      </button>
      <button
        @click="$emit('ver-facturas', casilla.casilla_codigo)"
        class="p-1.5 text-gray-500 hover:text-green-600 hover:bg-green-50 rounded"
        title="Ver facturas"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  casilla: { type: Object, required: true },
  soloLectura: { type: Boolean, default: false },
})

defineEmits(['ver-facturas', 'ajustar'])

// 🔹 Detectar si es un indicador comercial (Sección 9)
const isIndicator = computed(() => {
  return props.casilla.casilla_codigo?.startsWith('INDICADOR_') || 
         props.casilla.seccion === '9'
})

const esReferencia = computed(() => {
  return props.casilla.tipo_casilla === 'REFERENCIA' || 
         props.casilla.seccion === '4'
})

const formatValue = (value, withCurrency) => {
  const numValue = Number(value || 0)
  return numValue.toLocaleString('es-GT', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  })
}
</script>