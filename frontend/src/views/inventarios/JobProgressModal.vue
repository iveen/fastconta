<template>
  <div v-if="job" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
    <div class="bg-white rounded-xl shadow-2xl w-full max-w-lg p-6 animate-fade-in">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-bold text-gray-900">Procesando Importación</h3>
        <span :class="badgeClass" class="px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide">
          {{ job.estado }}
        </span>
      </div>

      <p class="text-sm text-gray-600 mb-4 truncate">{{ job.archivo_original }}</p>

      <!-- Barra de Progreso -->
      <div class="mb-6">
        <div class="flex justify-between text-sm font-medium text-gray-700 mb-1">
          <span>Progreso</span>
          <span>{{ job.porcentaje }}%</span>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
          <div 
            :class="barClass" 
            :style="{ width: `${job.porcentaje}%` }" 
            class="h-3 rounded-full transition-all duration-500 ease-out"
          ></div>
        </div>
      </div>

      <!-- Estadísticas en tiempo real -->
      <div class="grid grid-cols-3 gap-4 text-center mb-6">
        <div class="p-3 bg-gray-50 rounded-lg">
          <div class="text-xs text-gray-500">Procesadas</div>
          <div class="text-lg font-bold text-gray-900">{{ job.filas_procesadas }}</div>
        </div>
        <div class="p-3 bg-green-50 rounded-lg">
          <div class="text-xs text-green-700">Válidas</div>
          <div class="text-lg font-bold text-green-700">{{ job.filas_validas }}</div>
        </div>
        <div class="p-3 bg-red-50 rounded-lg">
          <div class="text-xs text-red-700">Errores</div>
          <div class="text-lg font-bold text-red-700">{{ job.filas_con_error }}</div>
        </div>
      </div>

      <!-- Mensaje de error si aplica -->
      <div v-if="job.mensaje_error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
        <p class="text-sm text-red-800 flex items-start gap-2">
          <span>⚠️</span> {{ job.mensaje_error }}
        </p>
      </div>

      <!-- Acciones -->
      <div class="flex justify-end gap-3">
        <button 
          v-if="job.estado === 'PENDIENTE'"
          @click="$emit('cancelar')"
          class="px-4 py-2 text-sm font-medium text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition-colors"
        >
          Cancelar
        </button>
        <button 
          v-if="['COMPLETADO', 'FALLIDO', 'CANCELADO'].includes(job.estado)"
          @click="$emit('cerrar')"
          class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Cerrar
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  job: { type: Object, required: true }
})

defineEmits(['cerrar', 'cancelar'])

const badgeClass = computed(() => {
  const map = {
    'PENDIENTE': 'bg-yellow-100 text-yellow-800',
    'PROCESANDO': 'bg-blue-100 text-blue-800',
    'COMPLETADO': 'bg-green-100 text-green-800',
    'FALLIDO': 'bg-red-100 text-red-800',
    'CANCELADO': 'bg-gray-100 text-gray-800',
    'TOMA_ELIMINADA': 'bg-purple-100 text-purple-800'
  }
  return map[props.job.estado] || 'bg-gray-100 text-gray-800'
})

const barClass = computed(() => {
  if (props.job.estado === 'FALLIDO') return 'bg-red-500'
  if (props.job.estado === 'COMPLETADO') return 'bg-green-500'
  return 'bg-blue-600'
})
</script>