<!-- src/components/fel/FELJobProgress.vue -->
<template>
  <div class="bg-white border border-gray-200 rounded-xl p-4">
    <div class="flex items-start justify-between gap-4 mb-3">
      <div class="flex items-center gap-3 min-w-0">
        <div :class="['w-10 h-10 rounded-full flex items-center justify-center shrink-0', statusBgClass]">
          <svg v-if="job.estado === 'PROCESANDO'" class="w-5 h-5 text-blue-600 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
          </svg>
          <span v-else class="text-lg">{{ statusIcon }}</span>
        </div>
        <div class="min-w-0">
          <p class="font-medium text-gray-900 truncate">{{ job.archivo_original }}</p>
          <p class="text-xs text-gray-500">
            {{ formatTime(job.created_at) }} · 
            <span :class="statusTextClass" class="font-semibold">{{ job.estado }}</span>
          </p>
        </div>
      </div>

      <div class="flex items-center gap-1 shrink-0">
        <button
          v-if="canCancel"
          @click="cancelJob"
          :disabled="actionLoading"
          class="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
          title="Cancelar"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
        </button>
        <button
          v-if="canReprocess"
          @click="reprocessJob(false)"
          :disabled="actionLoading"
          class="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors disabled:opacity-50"
          title="Reprocesar todo"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
          </svg>
        </button>
        <button
          v-if="canReprocess && job.facturas_con_error > 0"
          @click="reprocessJob(true)"
          :disabled="actionLoading"
          class="p-2 text-orange-600 hover:bg-orange-50 rounded-lg transition-colors disabled:opacity-50"
          title="Reprocesar solo errores"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Barra de progreso -->
    <div v-if="isProcessing" class="mb-3">
      <div class="flex items-center justify-between text-xs text-gray-600 mb-1">
        <span>{{ job.archivos_procesados }} / {{ job.archivos_totales }} archivos</span>
        <span class="font-semibold">{{ job.porcentaje }}%</span>
      </div>
      <div class="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
        <div
          class="bg-gradient-to-r from-blue-500 to-blue-600 h-2 rounded-full transition-all duration-500"
          :style="{ width: `${job.porcentaje}%` }"
        />
      </div>
    </div>

    <!-- Estadísticas -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
      <div class="bg-green-50 rounded-lg px-3 py-2">
        <p class="text-green-600 font-semibold">{{ job.facturas_creadas }}</p>
        <p class="text-green-700">Creadas</p>
      </div>
      <div class="bg-yellow-50 rounded-lg px-3 py-2">
        <p class="text-yellow-600 font-semibold">{{ job.facturas_duplicadas }}</p>
        <p class="text-yellow-700">Duplicadas</p>
      </div>
      <div class="bg-red-50 rounded-lg px-3 py-2">
        <p class="text-red-600 font-semibold">{{ job.facturas_con_error }}</p>
        <p class="text-red-700">Con error</p>
      </div>
      <div class="bg-gray-50 rounded-lg px-3 py-2">
        <p class="text-gray-600 font-semibold">{{ job.archivos_totales }}</p>
        <p class="text-gray-700">Total</p>
      </div>
    </div>

    <!-- Errores expandibles -->
    <div v-if="job.errores && job.errores.length > 0" class="mt-3">
      <button
        @click="showErrors = !showErrors"
        class="text-xs text-red-600 hover:text-red-700 font-medium flex items-center gap-1"
      >
        <svg v-if="!showErrors" class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
        </svg>
        <svg v-else class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"/>
        </svg>
        Ver {{ job.errores.length }} error(es)
      </button>
      <div v-if="showErrors" class="mt-2 bg-red-50 border border-red-200 rounded-lg p-2 max-h-40 overflow-y-auto">
        <div v-for="(err, idx) in job.errores" :key="idx" class="text-xs text-red-800 py-1">
          <span class="font-medium">{{ err.file }}:</span> {{ err.error }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { toast } from 'vue3-toastify'
import { felAPI } from '@/stores/fel'

const props = defineProps({
  job: { type: Object, required: true },
})

const emit = defineEmits(['updated', 'cancelled', 'reprocessed'])

const showErrors = ref(false)
const actionLoading = ref(false)
const localJob = ref({ ...props.job })
let pollInterval = null

const isProcessing = computed(() =>
  ['PENDIENTE', 'PROCESANDO'].includes(localJob.value.estado)
)
const canCancel = computed(() =>
  ['PENDIENTE', 'PROCESANDO'].includes(localJob.value.estado)
)
const canReprocess = computed(() =>
  ['FALLIDO', 'COMPLETADO', 'CANCELADO'].includes(localJob.value.estado)
)

const statusIcon = computed(() => ({
  PENDIENTE: '⏳', PROCESANDO: '⚙️', COMPLETADO: '✅', FALLIDO: '❌', CANCELADO: '⏹️',
}[localJob.value.estado] || '⏳'))

const statusBgClass = computed(() => ({
  PENDIENTE: 'bg-gray-100', PROCESANDO: 'bg-blue-100', COMPLETADO: 'bg-green-100',
  FALLIDO: 'bg-red-100', CANCELADO: 'bg-orange-100',
}[localJob.value.estado] || 'bg-gray-100'))

const statusTextClass = computed(() => ({
  PENDIENTE: 'text-gray-600', PROCESANDO: 'text-blue-600', COMPLETADO: 'text-green-600',
  FALLIDO: 'text-red-600', CANCELADO: 'text-orange-600',
}[localJob.value.estado] || 'text-gray-600'))

const formatTime = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('es-GT', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'
  })
}

const startPolling = () => {
  stopPolling()
  pollInterval = setInterval(async () => {
    try {
      const updated = await felAPI.getJobStatus(localJob.value.id)
      localJob.value = updated
      emit('updated', updated)

      if (!isProcessing.value) {
        stopPolling()
        if (updated.estado === 'COMPLETADO') {
          toast.success(`✅ ${updated.archivo_original}: ${updated.facturas_creadas} facturas creadas`)
        } else if (updated.estado === 'FALLIDO') {
          toast.error(`❌ ${updated.archivo_original}: ${updated.mensaje_error || 'Error desconocido'}`)
        } else if (updated.estado === 'CANCELADO') {
          toast.info(`⏹️ ${updated.archivo_original} cancelado`)
        }
      }
    } catch (error) {
      console.error('Error polling job:', error)
    }
  }, 2000)
}

const stopPolling = () => {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

const cancelJob = async () => {
  if (!confirm('¿Cancelar este job? Las facturas ya procesadas se mantendrán.')) return
  actionLoading.value = true
  try {
    const updated = await felAPI.cancelJob(localJob.value.id)
    localJob.value = updated
    emit('cancelled', updated)
    toast.info('⏹️ Job cancelado')
    stopPolling()
  } catch (error) {
    toast.error(error.response?.data?.detail || 'Error al cancelar')
  } finally {
    actionLoading.value = false
  }
}

const reprocessJob = async (soloErrores) => {
  actionLoading.value = true
  try {
    const result = await felAPI.reprocessJob(localJob.value.id, soloErrores)
    toast.success(`🔄 ${result.message}`)
    emit('reprocessed', result)
  } catch (error) {
    toast.error(error.response?.data?.detail || 'Error al reprocesar')
  } finally {
    actionLoading.value = false
  }
}

watch(() => props.job, (newJob) => {
  localJob.value = { ...newJob }
}, { deep: true })

onMounted(() => {
  if (isProcessing.value) startPolling()
})

onUnmounted(() => {
  stopPolling()
})
</script>