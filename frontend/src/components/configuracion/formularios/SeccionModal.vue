<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
      <!-- Header -->
      <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center sticky top-0 bg-white rounded-t-xl">
        <div>
          <h2 class="text-xl font-bold text-gray-800">{{ titulo }}</h2>
          <p class="text-sm text-gray-600 mt-1">
            Formulario {{ formularioCodigo }}
          </p>
        </div>
        <button @click="$emit('cancelar')" class="text-gray-400 hover:text-gray-600">
          <X class="w-6 h-6" />
        </button>
      </div>

      <!-- Form -->
      <form @submit.prevent="handleSubmit" class="p-6 space-y-6">
        <!-- Identificación -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Número de Sección <span class="text-red-500">*</span>
            </label>
            <input
              v-model="form.numero_seccion"
              type="text"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Ej: 3"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Orden
            </label>
            <input
              v-model.number="form.orden"
              type="number"
              min="0"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="0"
            />
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Título <span class="text-red-500">*</span>
          </label>
          <input
            v-model="form.titulo"
            type="text"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Título de la sección"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
          <textarea
            v-model="form.descripcion"
            rows="2"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Descripción de la sección"
          ></textarea>
        </div>

        <!-- Configuración -->
        <div class="border-t border-gray-200 pt-4">
          <h3 class="text-sm font-semibold text-gray-700 mb-3">Configuración</h3>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Tipo de Sección <span class="text-red-500">*</span>
            </label>
            <select
              v-model="form.tipo_seccion"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Seleccione...</option>
              <option value="IDENTIFICACION">Identificación</option>
              <option value="PERIODO">Período</option>
              <option value="DEBITO_FISCAL">Débito Fiscal</option>
              <option value="CREDITO_FISCAL">Crédito Fiscal</option>
              <option value="EXPORTACIONES">Exportaciones</option>
              <option value="DETERMINACION">Determinación</option>
              <option value="INFORMATIVA">Informativa</option>
              <option value="RECTIFICACION">Rectificación</option>
              <option value="ACCESORIOS">Accesorios</option>
            </select>
          </div>
        </div>

        <!-- Banderas -->
        <div class="border-t border-gray-200 pt-4">
          <h3 class="text-sm font-semibold text-gray-700 mb-3">Opciones</h3>
          
          <div class="space-y-2">
            <label class="flex items-center">
              <input
                v-model="form.es_obligatoria"
                type="checkbox"
                class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span class="ml-2 text-sm text-gray-700">Sección obligatoria</span>
            </label>

            <label class="flex items-center">
              <input
                v-model="form.requiere_exportador"
                type="checkbox"
                class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span class="ml-2 text-sm text-gray-700">Requiere datos de exportador</span>
            </label>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex justify-end gap-3 pt-4 border-t border-gray-200 sticky bottom-0 bg-white">
          <button
            type="button"
            @click="$emit('cancelar')"
            class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Cancelar
          </button>
          <button
            type="submit"
            :disabled="loading"
            class="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ loading ? 'Guardando...' : 'Guardar' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue'
import { X } from '@lucide/vue'

const props = defineProps({
  titulo: { type: String, required: true },
  data: { type: Object, default: null },
  formularioId: { type: String, default: null },
  formularioCodigo: { type: String, default: '' },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['cancelar', 'guardar'])

const form = reactive({
  numero_seccion: '',
  titulo: '',
  descripcion: '',
  orden: 0,
  tipo_seccion: '',
  es_obligatoria: true,
  requiere_exportador: false,
})

watch(
  () => props.data,
  (val) => {
    if (val) {
      Object.assign(form, {
        numero_seccion: val.numero_seccion || '',
        titulo: val.titulo || '',
        descripcion: val.descripcion || '',
        orden: val.orden || 0,
        tipo_seccion: val.tipo_seccion || '',
        es_obligatoria: val.es_obligatoria !== undefined ? val.es_obligatoria : true,
        requiere_exportador: val.requiere_exportador || false,
      })
    }
  },
  { immediate: true }
)

function handleSubmit() {
  emit('guardar', { ...form, formulario_id: props.formularioId })
}
</script>