<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-xl shadow-xl max-w-lg w-full">
      <div class="px-6 py-4 border-b border-gray-200">
        <h2 class="text-xl font-bold text-gray-800">Duplicar Formulario</h2>
        <p class="text-sm text-gray-600 mt-1">
          Crear nueva versión desde {{ formulario.codigo }} v{{ formulario.version }}
        </p>
      </div>

      <form @submit.prevent="handleSubmit" class="p-6 space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Nueva versión <span class="text-red-500">*</span>
          </label>
          <input
            v-model="form.nueva_version"
            type="text"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Ej: 2.0"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Fecha de vigencia <span class="text-red-500">*</span>
          </label>
          <input
            v-model="form.fecha_vigencia_desde"
            type="date"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div class="space-y-3 pt-2">
          <p class="text-sm font-medium text-gray-700">Copiar elementos:</p>
          
          <label class="flex items-center">
            <input v-model="form.copiar_secciones" type="checkbox" class="w-4 h-4 text-blue-600 rounded" />
            <span class="ml-2 text-sm text-gray-700">Secciones</span>
          </label>
          
          <label class="flex items-center">
            <input v-model="form.copiar_casillas" type="checkbox" class="w-4 h-4 text-blue-600 rounded" />
            <span class="ml-2 text-sm text-gray-700">Casillas</span>
          </label>
          
          <label class="flex items-center">
            <input v-model="form.copiar_reglas_filtrado" type="checkbox" class="w-4 h-4 text-blue-600 rounded" />
            <span class="ml-2 text-sm text-gray-700">Reglas de filtrado</span>
          </label>
          
          <label class="flex items-center">
            <input v-model="form.copiar_exclusiones" type="checkbox" class="w-4 h-4 text-blue-600 rounded" />
            <span class="ml-2 text-sm text-gray-700">Exclusiones</span>
          </label>
        </div>

        <div class="flex justify-end gap-3 pt-4 border-t border-gray-200">
          <button
            type="button"
            @click="$emit('cancelar')"
            class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Cancelar
          </button>
          <button
            type="submit"
            :disabled="loading"
            class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {{ loading ? 'Duplicando...' : 'Duplicar' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({
  formulario: { type: Object, required: true },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['cancelar', 'duplicar'])

const form = reactive({
  nueva_version: '',
  fecha_vigencia_desde: new Date().toISOString().split('T')[0],
  copiar_casillas: true,
  copiar_secciones: true,
  copiar_reglas_filtrado: true,
  copiar_exclusiones: true,
})

function handleSubmit() {
  emit('duplicar', { ...form })
}
</script>