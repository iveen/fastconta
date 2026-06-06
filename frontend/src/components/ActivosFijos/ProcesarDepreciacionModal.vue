<template>
  <div v-if="isOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
      <h3 class="text-lg font-bold text-gray-800 mb-4">Procesar Depreciación Mensual</h3>
      
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Empresa</label>
          <input type="text" :value="nombreEmpresa" disabled class="w-full px-3 py-2 border rounded-md bg-gray-100 text-gray-600" />
        </div>
        
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Año</label>
            <input v-model="anio" type="number" min="2020" max="2099" class="w-full px-3 py-2 border rounded-md focus:ring-indigo-500 focus:border-indigo-500" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Mes</label>
            <select v-model="mes" class="w-full px-3 py-2 border rounded-md focus:ring-indigo-500 focus:border-indigo-500">
              <option v-for="m in 12" :key="m" :value="m">{{ obtenerNombreMes(m) }}</option>
            </select>
          </div>
        </div>

        <div class="bg-yellow-50 border border-yellow-200 text-yellow-800 text-sm p-3 rounded-md">
          ⚠️ Esta acción generará una partida de diario en estado "Borrador" con la depreciación de todos los activos elegibles.
        </div>
      </div>

      <div class="flex justify-end gap-3 mt-6">
        <button @click="$emit('close')" :disabled="loading" class="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 disabled:opacity-50">
          Cancelar
        </button>
        <button @click="procesar" :disabled="loading" class="px-4 py-2 text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2">
          <span v-if="loading" class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
          {{ loading ? 'Procesando...' : 'Generar Partida' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useActivosFijosStore } from '@/stores/activosFijos'

const props = defineProps({
  isOpen: Boolean,
  empresaId: String,
  nombreEmpresa: String
})

const emit = defineEmits(['close', 'success'])
const store = useActivosFijosStore()

const anio = ref(new Date().getFullYear())
const mes = ref(new Date().getMonth() + 1)
const loading = ref(false)

const meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
const obtenerNombreMes = (m) => meses[m - 1]

const procesar = async () => {
  loading.value = true
  try {
    const resultado = await store.procesarDepreciacionMensual(props.empresaId, anio.value, mes.value)
    alert(`Éxito: ${resultado.mensaje}`)
    emit('success')
    emit('close')
  } catch (error) {
    alert('Error: ' + (error.response?.data?.detail || 'No se pudo procesar la depreciación'))
  } finally {
    loading.value = false
  }
}
</script>