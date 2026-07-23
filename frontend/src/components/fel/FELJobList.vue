<!-- src/components/fel/FELJobList.vue -->
<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-gray-900">Historial de Importaciones</h3>
      <div class="flex items-center gap-2">
        <select
          v-model="filterEstado"
          class="text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Todos los estados</option>
          <option value="PENDIENTE">Pendiente</option>
          <option value="PROCESANDO">Procesando</option>
          <option value="COMPLETADO">Completado</option>
          <option value="FALLIDO">Fallido</option>
          <option value="CANCELADO">Cancelado</option>
        </select>
        <button
          @click="loadJobs"
          :disabled="loading"
          class="p-1.5 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
          title="Recargar"
        >
          <svg :class="['w-4 h-4', loading && 'animate-spin']" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
          </svg>
        </button>
      </div>
    </div>

    <div v-if="loading && jobs.length === 0" class="text-center py-12 text-gray-500">
      <svg class="w-8 h-8 animate-spin mx-auto mb-2 text-blue-600" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
      </svg>
      <p>Cargando jobs...</p>
    </div>

    <div v-else-if="jobs.length === 0" class="text-center py-12 text-gray-500">
      <span class="text-5xl block mb-2">📦</span>
      <p>No hay importaciones registradas</p>
    </div>

    <div v-else class="space-y-3">
      <FELJobProgress
        v-for="job in jobs"
        :key="job.id"
        :job="job"
        @updated="onJobUpdated"
        @cancelled="onJobUpdated"
        @reprocessed="onJobReprocessed"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { felAPI } from '@/stores/fel'
import { useCompanyStore } from '@/stores/company'
import FELJobProgress from './FELJobProgress.vue'

const companyStore = useCompanyStore()

const jobs = ref([])
const loading = ref(false)
const filterEstado = ref('')

const loadJobs = async () => {
  loading.value = true
  try {
    const params = { limit: 50 }
    if (companyStore.selectedCompanyId) {
      params.empresa_id = companyStore.selectedCompanyId
    }
    if (filterEstado.value) {
      params.estado = filterEstado.value
    }
    jobs.value = await felAPI.getJobs(params)
  } catch (error) {
    console.error('Error cargando jobs:', error)
  } finally {
    loading.value = false
  }
}

const onJobUpdated = (updatedJob) => {
  const idx = jobs.value.findIndex(j => j.id === updatedJob.id)
  if (idx !== -1) jobs.value[idx] = updatedJob
}

const onJobReprocessed = () => {
  loadJobs()
}

const addJob = (job) => {
  jobs.value.unshift(job)
}

watch(() => companyStore.selectedCompanyId, () => { loadJobs() })
watch(filterEstado, () => { loadJobs() })

onMounted(() => { loadJobs() })

defineExpose({ addJob, reload: loadJobs })
</script>