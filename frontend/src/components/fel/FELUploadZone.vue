<!-- src/components/fel/FELUploadZone.vue -->
<template>
  <div
    @dragover.prevent="onDragOver"
    @dragleave.prevent="isDragging = false"
    @drop.prevent="onDrop"
    :class="[
      'relative border-2 border-dashed rounded-xl p-8 text-center transition-all',
      isDragging
        ? 'border-blue-500 bg-blue-50 scale-[1.01]'
        : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
    ]"
  >
    <input
      ref="fileInput"
      type="file"
      multiple
      accept=".xml,.pdf,.zip"
      class="hidden"
      @change="onFileSelect"
    />

    <div class="flex flex-col items-center gap-3">
      <div :class="[
        'w-16 h-16 rounded-full flex items-center justify-center transition-colors',
        isDragging ? 'bg-blue-100' : 'bg-gray-100'
      ]">
        <svg class="w-8 h-8" :class="isDragging ? 'text-blue-600' : 'text-gray-500'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
        </svg>
      </div>

      <div>
        <p class="text-base font-medium text-gray-700">
          Arrastra tus archivos aquí o
          <button
            @click="$refs.fileInput.click()"
            class="text-blue-600 font-semibold hover:text-blue-700"
          >
            selecciona archivos
          </button>
        </p>
        <p class="text-sm text-gray-500 mt-1">
          ZIP del SAT (múltiples XML), XML individuales o PDFs
        </p>
      </div>
    </div>

    <!-- Preview de archivos seleccionados -->
    <div v-if="selectedFiles.length > 0" class="mt-6 border-t border-gray-200 pt-4">
      <div class="flex items-center justify-between mb-3">
        <p class="text-sm font-medium text-gray-700">
          {{ selectedFiles.length }} archivo(s) seleccionado(s)
        </p>
        <button
          @click="clearFiles"
          class="text-sm text-red-600 hover:text-red-700 font-medium"
        >
          Limpiar
        </button>
      </div>

      <div class="space-y-2 max-h-48 overflow-y-auto">
        <div
          v-for="file in selectedFiles"
          :key="file.name"
          class="flex items-center justify-between bg-white border border-gray-200 rounded-lg px-3 py-2"
        >
          <div class="flex items-center gap-2 min-w-0">
            <span class="text-lg shrink-0">{{ getFileIcon(file.name) }}</span>
            <span class="text-sm text-gray-700 truncate">{{ file.name }}</span>
            <span class="text-xs text-gray-400 shrink-0">{{ formatSize(file.size) }}</span>
          </div>
          <button
            @click="removeFile(file.name)"
            class="text-gray-400 hover:text-red-600 shrink-0 ml-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
      </div>

      <button
        @click="uploadFiles"
        :disabled="uploading"
        class="mt-4 w-full bg-blue-600 text-white px-4 py-2.5 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
      >
        <svg v-if="uploading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
        </svg>
        <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
        </svg>
        {{ uploading ? 'Subiendo...' : 'Subir archivos' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { toast } from 'vue3-toastify'
import { felAPI } from '@/stores/fel'
import { useCompanyStore } from '@/stores/company'
import { useAuthStore } from '@/stores/auth'

const emit = defineEmits(['job-created', 'upload-complete'])

const companyStore = useCompanyStore()
const authStore = useAuthStore()

const isDragging = ref(false)
const selectedFiles = ref([])
const uploading = ref(false)
const fileInput = ref(null)

const onDragOver = () => { isDragging.value = true }
const onDrop = (e) => {
  isDragging.value = false
  addFiles(Array.from(e.dataTransfer.files))
}
const onFileSelect = (e) => {
  addFiles(Array.from(e.target.files || []))
}

const addFiles = (files) => {
  const validExts = ['xml', 'pdf', 'zip']
  const validFiles = files.filter(f => {
    const ext = f.name.split('.').pop().toLowerCase()
    return validExts.includes(ext)
  })

  if (validFiles.length !== files.length) {
    toast.warning('Algunos archivos fueron ignorados (solo XML, PDF, ZIP)')
  }

  validFiles.forEach(f => {
    if (!selectedFiles.value.find(sf => sf.name === f.name)) {
      selectedFiles.value.push(f)
    }
  })
}

const removeFile = (filename) => {
  selectedFiles.value = selectedFiles.value.filter(f => f.name !== filename)
}

const clearFiles = () => {
  selectedFiles.value = []
  if (fileInput.value) fileInput.value.value = ''
}

const uploadFiles = async () => {
  if (selectedFiles.value.length === 0) return

  const empresaId = companyStore.selectedCompanyId
  if (!empresaId) {
    toast.error('Debes seleccionar una empresa primero')
    return
  }

  uploading.value = true
  try {
    const result = await felAPI.uploadFacturas(selectedFiles.value, empresaId)

    if (result.cargadas > 0) {
      toast.success(`✅ ${result.cargadas} factura(s) cargada(s) exitosamente`)
    }

    if (result.jobs_background && result.jobs_background.length > 0) {
      result.jobs_background.forEach(job => {
        toast.info(`📦 ${job.filename}: ${job.total_files} XMLs en cola de procesamiento`)
        emit('job-created', job)
      })
    }

    if (result.rechazadas && result.rechazadas.length > 0) {
      toast.warning(`⚠️ ${result.rechazadas.length} archivo(s) rechazado(s)`)
    }

    emit('upload-complete', result)
    clearFiles()
  } catch (error) {
    console.error('Error subiendo archivos:', error)
    toast.error(error.response?.data?.detail || 'Error al subir archivos')
  } finally {
    uploading.value = false
  }
}

const getFileIcon = (filename) => {
  const ext = filename.split('.').pop().toLowerCase()
  if (ext === 'zip') return '📦'
  if (ext === 'pdf') return '📄'
  if (ext === 'xml') return '📋'
  return '📎'
}

const formatSize = (bytes) => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
</script>