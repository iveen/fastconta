<!-- src/components/DateInput.vue -->
<template>
  <div class="relative">
    <input
      :value="formattedValue"
      @input="handleInput"
      @blur="handleBlur"
      @focus="$emit('focus', $event)"
      :placeholder="placeholder"
      :disabled="disabled"
      :class="[
        'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
        disabled ? 'bg-gray-100 cursor-not-allowed' : ''
      ]"
      maxlength="10"
    />
    <!-- Icono de calendario -->
    <button
      v-if="!disabled"
      @click="showPicker = !showPicker"
      type="button"
      class="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    </button>
    
    <!-- Date picker nativo oculto -->
    <input
      v-if="showPicker"
      ref="nativePicker"
      type="date"
      :value="modelValue"
      @change="handleNativeChange"
      class="absolute opacity-0 pointer-events-none"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  modelValue: String, // Formato ISO: yyyy-mm-dd
  placeholder: { type: String, default: 'dd/mm/yyyy' },
  disabled: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue', 'focus'])

const showPicker = ref(false)
const nativePicker = ref(null)
const displayValue = ref('')

// Formatear fecha ISO a dd/mm/yyyy
const formattedValue = computed(() => {
  if (!props.modelValue) return ''
  const [year, month, day] = props.modelValue.split('-')
  if (!year || !month || !day) return ''
  return `${day}/${month}/${year}`
})

// Manejar entrada manual
const handleInput = (event) => {
  let value = event.target.value.replace(/\D/g, '') // Solo números
  
  // Agregar slashes automáticamente
  if (value.length >= 2 && value.length <= 4) {
    value = `${value.slice(0, 2)}/${value.slice(2)}`
  } else if (value.length > 4) {
    value = `${value.slice(0, 2)}/${value.slice(2, 4)}/${value.slice(4, 8)}`
  }
  
  displayValue.value = value
  
  // Validar y emitir si es fecha completa
  if (value.length === 10) {
    const [day, month, year] = value.split('/')
    if (day && month && year) {
      const isoDate = `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`
      if (isValidDate(isoDate)) {
        emit('update:modelValue', isoDate)
      }
    }
  }
}

// Manejar cambio desde el picker nativo
const handleNativeChange = (event) => {
  const isoDate = event.target.value
  if (isoDate) {
    emit('update:modelValue', isoDate)
    const [year, month, day] = isoDate.split('-')
    displayValue.value = `${day}/${month}/${year}`
  }
  showPicker.value = false
}

// Manejar blur para formatear
const handleBlur = () => {
  if (props.modelValue) {
    displayValue.value = formattedValue.value
  }
}

// Validar fecha
const isValidDate = (dateString) => {
  const date = new Date(dateString)
  return date instanceof Date && !isNaN(date)
}

// Sincronizar displayValue cuando cambia modelValue desde fuera
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    const [year, month, day] = newVal.split('-')
    displayValue.value = `${day}/${month}/${year}`
  } else {
    displayValue.value = ''
  }
}, { immediate: true })
</script>