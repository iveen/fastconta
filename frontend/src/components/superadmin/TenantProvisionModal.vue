<template>
  <Teleport to="body">
    <div v-if="isVisible" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden">
        <!-- Header -->
        <div class="bg-gradient-to-r from-blue-600 to-emerald-600 px-6 py-4">
          <h3 class="text-xl font-bold text-white flex items-center gap-2">
            <Server class="w-6 h-6" />
            Creando Nuevo Tenant
          </h3>
          <p class="text-blue-100 text-sm mt-1">
            Este proceso puede tardar entre 30 segundos y 2 minutos
          </p>
        </div>

        <!-- Steps -->
        <div class="p-6">
          <div class="space-y-4">
            <div
              v-for="(step, index) in steps"
              :key="index"
              class="flex items-start gap-4 p-3 rounded-lg transition-all duration-300"
              :class="getStepClass(step)"
            >
              <!-- Icon -->
              <div class="flex-shrink-0 mt-0.5">
                <!-- Processing -->
                <div v-if="step.status === 'processing'" class="relative">
                  <div class="w-8 h-8 rounded-full border-4 border-blue-200 border-t-blue-600 animate-spin"></div>
                </div>
                <!-- Pending -->
                <div v-else-if="step.status === 'pending'" class="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                  <Clock class="w-4 h-4 text-gray-400" />
                </div>
                <!-- Success -->
                <div v-else-if="step.status === 'success'" class="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center">
                  <Check class="w-5 h-5 text-white" />
                </div>
                <!-- Error -->
                <div v-else-if="step.status === 'error'" class="w-8 h-8 rounded-full bg-red-500 flex items-center justify-center">
                  <X class="w-5 h-5 text-white" />
                </div>
              </div>

              <!-- Content -->
              <div class="flex-1 min-w-0">
                <p class="font-semibold text-gray-900">{{ step.title }}</p>
                <p class="text-sm text-gray-600 mt-0.5">{{ step.message }}</p>
              </div>
            </div>
          </div>

          <!-- Progress Bar -->
          <div class="mt-6 pt-4 border-t">
            <div class="flex justify-between text-sm text-gray-600 mb-2">
              <span>Progreso</span>
              <span>{{ progressPercentage }}%</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
              <div
                class="h-full bg-gradient-to-r from-blue-500 to-emerald-500 transition-all duration-500 ease-out"
                :style="{ width: `${progressPercentage}%` }"
              ></div>
            </div>
          </div>

          <!-- Warning -->
          <div v-if="currentStep.status === 'processing'" class="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2">
            <AlertTriangle class="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <p class="text-sm text-amber-800">
              <strong>No cierres esta ventana.</strong> El proceso debe completarse para crear correctamente el tenant.
            </p>
          </div>

          <!-- Success Message -->
          <div v-if="currentStep.status === 'success'" class="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
            <div class="flex items-center gap-2 mb-2">
              <CheckCircle class="w-5 h-5 text-green-600" />
              <p class="font-semibold text-green-900">¡Completado!</p>
            </div>
            <p class="text-sm text-green-800">
              El tenant ha sido creado exitosamente. El administrador puede iniciar sesión con las credenciales proporcionadas.
            </p>
          </div>

          <!-- Error Message -->
          <div v-if="currentStep.status === 'error'" class="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div class="flex items-center gap-2 mb-2">
              <AlertCircle class="w-5 h-5 text-red-600" />
              <p class="font-semibold text-red-900">Error en el proceso</p>
            </div>
            <p class="text-sm text-red-800 mb-3">{{ currentStep.message }}</p>
            <p class="text-xs text-red-700">
              El sistema ha realizado un rollback automático. Puedes intentar nuevamente.
            </p>
          </div>
        </div>

        <!-- Footer -->
        <div class="px-6 py-4 bg-gray-50 border-t flex justify-end gap-2">
          <button
            v-if="currentStep.status === 'success' || currentStep.status === 'error'"
            @click="close"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
          >
            {{ currentStep.status === 'success' ? 'Cerrar' : 'Reintentar' }}
          </button>
          <button
            v-else
            disabled
            class="px-4 py-2 bg-gray-300 text-gray-500 rounded-lg cursor-not-allowed"
          >
            Procesando...
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { Server, Clock, Check, X, AlertTriangle, CheckCircle, AlertCircle } from '@lucide/vue'

const props = defineProps({
  isVisible: {
    type: Boolean,
    default: false
  },
  currentStep: {
    type: Object,
    default: () => ({
      step: 1,
      total: 4,
      message: 'Iniciando...',
      status: 'pending'
    })
  }
})

const emit = defineEmits(['close'])

const steps = computed(() => [
  {
    title: 'Paso 1: Validación',
    message: props.currentStep.step >= 1 ? 'Verificando datos y permisos' : 'Esperando...',
    status: getStepStatus(1)
  },
  {
    title: 'Paso 2: Crear Schema',
    message: props.currentStep.step >= 2 ? 'Creando estructura en PostgreSQL' : 'Esperando...',
    status: getStepStatus(2)
  },
  {
    title: 'Paso 3: Migraciones',
    message: props.currentStep.step >= 3 ? 'Ejecutando migraciones de Alembic' : 'Esperando...',
    status: getStepStatus(3)
  },
  {
    title: 'Paso 4: Usuario Admin',
    message: props.currentStep.step >= 4 ? 'Creando cuenta de administrador' : 'Esperando...',
    status: getStepStatus(4)
  }
])

const progressPercentage = computed(() => {
  if (props.currentStep.status === 'error') return 0
  if (props.currentStep.status === 'success') return 100
  return Math.round(((props.currentStep.step - 1) / props.currentStep.total) * 100)
})

function getStepStatus(stepNumber) {
  if (props.currentStep.status === 'error' && stepNumber === props.currentStep.step) {
    return 'error'
  }
  if (props.currentStep.status === 'success') {
    return 'success'
  }
  if (stepNumber < props.currentStep.step) {
    return 'success'
  }
  if (stepNumber === props.currentStep.step) {
    return props.currentStep.status
  }
  return 'pending'
}

function getStepClass(step) {
  if (step.status === 'processing') return 'bg-blue-50 border border-blue-200'
  if (step.status === 'success') return 'bg-green-50 border border-green-200'
  if (step.status === 'error') return 'bg-red-50 border border-red-200'
  return 'bg-gray-50 border border-gray-200'
}

function close() {
  emit('close')
}
</script>