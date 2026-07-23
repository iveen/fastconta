<!-- src/components/fel/FELJobsPanel.vue -->
<template>
  <div class="space-y-6">
    <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <div class="flex items-start gap-3">
        <span class="text-2xl">💡</span>
        <div class="text-sm text-blue-800">
          <p class="font-semibold mb-1">Importación masiva de FEL</p>
          <p>
            Sube el ZIP descargado del SAT con todas las facturas electrónicas. 
            El procesamiento se realiza en segundo plano y recibirás una notificación 
            por email cuando termine. También puedes subir XMLs o PDFs individuales.
          </p>
        </div>
      </div>
    </div>

    <FELUploadZone
      @job-created="onJobCreated"
      @upload-complete="onUploadComplete"
    />

    <FELJobList ref="jobsListRef" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import FELUploadZone from './FELUploadZone.vue'
import FELJobList from './FELJobList.vue'

const jobsListRef = ref(null)

const onJobCreated = (job) => {
  if (jobsListRef.value) jobsListRef.value.addJob(job)
}

const onUploadComplete = () => {
  if (jobsListRef.value) jobsListRef.value.reload()
}
</script>