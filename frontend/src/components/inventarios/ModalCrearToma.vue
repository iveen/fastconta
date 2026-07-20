<!-- src/components/inventarios/ModalCrearToma.vue -->
<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
    <div class="bg-white rounded-xl shadow-2xl w-full max-w-xl p-6">
      <h3 class="text-lg font-bold text-gray-900 mb-4">Nueva Toma de Inventario</h3>

      <form @submit.prevent="guardar" class="space-y-4">
        <!-- Empresa -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Empresa *</label>
          <select v-model="form.empresa_public_id" required class="w-full px-3 py-2 border border-gray-300 rounded-md">
            <option value="">-- Selecciona --</option>
            <option v-for="emp in empresas" :key="emp.public_id" :value="emp.public_id">
              {{ emp.nombre }}
            </option>
          </select>
        </div>

        <!-- Período -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Año Fiscal *</label>
            <input v-model.number="form.anio_periodo" type="number" min="2000" max="2100" required class="w-full px-3 py-2 border border-gray-300 rounded-md" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Mes Fiscal *</label>
            <select v-model.number="form.mes_periodo" required class="w-full px-3 py-2 border border-gray-300 rounded-md">
              <option v-for="m in 12" :key="m" :value="m">{{ String(m).padStart(2, '0') }} - {{ nombresMeses[m-1] }}</option>
            </select>
          </div>
        </div>

        <!-- Fecha de corte -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Fecha de Corte *</label>
          <input v-model="form.fecha_corte" type="date" required class="w-full px-3 py-2 border border-gray-300 rounded-md" />
          <p v-if="form.tipo === 'FISCAL'" class="mt-1 text-xs text-blue-600">
            💡 Para inventario fiscal, la fecha debe ser 30/jun o 31/dic
          </p>
        </div>

        <!-- Tipo y Método -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Tipo *</label>
            <select v-model="form.tipo" required class="w-full px-3 py-2 border border-gray-300 rounded-md">
              <option value="FISCAL">Fiscal (30/jun o 31/dic)</option>
              <option value="INTERNO">Interno</option>
              <option value="AJUSTE">Ajuste</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Método Valuación *</label>
            <select v-model="form.metodo_valuacion" required class="w-full px-3 py-2 border border-gray-300 rounded-md">
              <option value="COSTO_PROMEDIO">Costo Promedio</option>
              <option value="PEPS">PEPS</option>
              <option value="IDENTIFICACION_ESPECIFICA">Identificación Específica</option>
            </select>
          </div>
        </div>

        <!-- Observaciones -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Observaciones</label>
          <textarea v-model="form.observaciones" rows="3" class="w-full px-3 py-2 border border-gray-300 rounded-md"></textarea>
        </div>

        <p v-if="error" class="text-sm text-red-600 bg-red-50 p-3 rounded-md">{{ error }}</p>

        <!-- Botones -->
        <div class="flex justify-end gap-3 pt-4 border-t">
          <button type="button" @click="$emit('close')" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">
            Cancelar
          </button>
          <button type="submit" :disabled="cargando" class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2">
            <span v-if="cargando" class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
            {{ cargando ? 'Creando...' : 'Crear Toma' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { inventarioService } from '@/services/inventarioService'
import { toast } from 'vue3-toastify'

const props = defineProps({
  empresas: { type: Array, required: true }
})
const emit = defineEmits(['close', 'creado'])

const nombresMeses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                      'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

const form = ref({
  empresa_public_id: '',
  anio_periodo: new Date().getFullYear(),
  mes_periodo: 6,
  fecha_corte: '',
  tipo: 'FISCAL',
  metodo_valuacion: 'COSTO_PROMEDIO',
  observaciones: ''
})
const cargando = ref(false)
const error = ref(null)

async function guardar() {
  cargando.value = true
  error.value = null
  try {
    await inventarioService.crearToma(form.value)
    toast.success('Toma creada exitosamente')
    emit('creado')
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al crear la toma'
  } finally {
    cargando.value = false
  }
}
</script>