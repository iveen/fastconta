<template>
  <div class="relative">
    <!-- Input de búsqueda -->
    <input 
      v-model="busqueda"
      @focus="mostrarDropdown = true"
      @input="mostrarDropdown = true"
      type="text"
      :placeholder="placeholder"
      class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
    />
    <!-- Icono de limpiar -->
    <button 
      v-if="cuentaSeleccionada" 
      @click="limpiar"
      class="absolute right-2 top-2.5 text-gray-400 hover:text-gray-600"
      title="Limpiar selección"
    >
      ✕
    </button>

    <!-- Dropdown de resultados -->
    <div 
      v-if="mostrarDropdown && cuentasFiltradas.length > 0" 
      class="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-y-auto"
    >
      <div 
        v-for="cuenta in cuentasFiltradas" 
        :key="cuenta.id"
        @click="seleccionarCuenta(cuenta)"
        class="px-4 py-2 hover:bg-indigo-50 cursor-pointer flex justify-between items-center"
      >
        <span class="font-mono text-sm font-semibold text-indigo-700">{{ cuenta.codigo }}</span>
        <span class="text-sm text-gray-700">{{ cuenta.nombre }}</span>
      </div>
    </div>

    <!-- Mensaje si no hay resultados -->
    <div 
      v-if="mostrarDropdown && busqueda && cuentasFiltradas.length === 0" 
      class="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg p-3 text-sm text-gray-500 text-center"
    >
      No se encontraron cuentas.
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  modelValue: String, // El ID de la cuenta seleccionada
  cuentas: { type: Array, default: () => [] },
  placeholder: { type: String, default: 'Buscar cuenta...' }
})

const emit = defineEmits(['update:modelValue'])

const busqueda = ref('')
const mostrarDropdown = ref(false)
const cuentaSeleccionada = ref(null)

// ✅ CORRECCIÓN: Primero eliminar duplicados, luego filtrar por búsqueda
const cuentasUnicas = computed(() => {
  return props.cuentas.filter((cuenta, index, self) =>
    index === self.findIndex((c) => c.id === cuenta.id)
  )
})

// Filtrar cuentas por código o nombre (insensible a mayúsculas)
const cuentasFiltradas = computed(() => {
  if (!busqueda.value) return cuentasUnicas.value.slice(0, 10)
  const query = busqueda.value.toLowerCase()
  return cuentasUnicas.value.filter(c => 
    c.codigo.toLowerCase().includes(query) || 
    c.nombre.toLowerCase().includes(query)
  ).slice(0, 15) // Limitar a 15 resultados para rendimiento
})

const seleccionarCuenta = (cuenta) => {
  cuentaSeleccionada.value = cuenta
  busqueda.value = `${cuenta.codigo} - ${cuenta.nombre}`
  emit('update:modelValue', cuenta.id)
  mostrarDropdown.value = false
}

const limpiar = () => {
  cuentaSeleccionada.value = null
  busqueda.value = ''
  emit('update:modelValue', '')
}

// Si el valor cambia desde fuera (ej: al editar), actualizar la vista
watch(() => props.modelValue, (nuevoId) => {
  if (!nuevoId) {
    limpiar()
    return
  }
  const encontrada = cuentasUnicas.value.find(c => c.id === nuevoId)
  if (encontrada) {
    cuentaSeleccionada.value = encontrada
    busqueda.value = `${encontrada.codigo} - ${encontrada.nombre}`
  }
}, { immediate: true })
</script>