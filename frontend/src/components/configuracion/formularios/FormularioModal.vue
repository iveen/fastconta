<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
      <!-- Header -->
      <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
        <h2 class="text-xl font-bold text-gray-800">{{ titulo }}</h2>
        <button @click="$emit('cancelar')" class="text-gray-400 hover:text-gray-600">
          <X class="w-6 h-6" />
        </button>
      </div>

      <!-- Form -->
      <form @submit.prevent="handleSubmit" class="p-6 space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Código <span class="text-red-500">*</span>
            </label>
            <input
              v-model="form.codigo"
              type="text"
              required
              :disabled="isEdit"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
              placeholder="Ej: SAT-2237"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Versión <span class="text-red-500">*</span>
            </label>
            <input
              v-model="form.version"
              type="text"
              required
              :disabled="isEdit"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
              placeholder="Ej: 1.0"
            />
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Nombre <span class="text-red-500">*</span>
          </label>
          <input
            v-model="form.nombre"
            type="text"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Nombre del formulario"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
          <textarea
            v-model="form.descripcion"
            rows="3"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Descripción del formulario"
          ></textarea>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Vigencia desde <span class="text-red-500">*</span>
            </label>
            <input
              v-model="form.fecha_vigencia_desde"
              type="date"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Vigencia hasta</label>
            <input
              v-model="form.fecha_vigencia_hasta"
              type="date"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        <div class="flex items-center">
          <input
            v-model="form.es_version_activa"
            type="checkbox"
            id="es_activo"
            class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
          <label for="es_activo" class="ml-2 text-sm text-gray-700">
            Versión activa
          </label>
        </div>

        <!-- Actions -->
        <div class="flex justify-end gap-3 pt-4 border-t border-gray-200">
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
import { ref, reactive, computed, watch } from 'vue'
import { X } from '@lucide/vue'

const props = defineProps({
  titulo: { type: String, required: true },
  data: { type: Object, default: null },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['cancelar', 'guardar'])

const isEdit = computed(() => !!props.data)

const form = reactive({
  codigo: '',
  version: '',
  nombre: '',
  descripcion: '',
  fecha_vigencia_desde: '',
  fecha_vigencia_hasta: '',
  es_version_activa: true,
})

watch(
  () => props.data,
  (val) => {
    if (val) {
      Object.assign(form, {
        codigo: val.codigo,
        version: val.version,
        nombre: val.nombre,
        descripcion: val.descripcion || '',
        fecha_vigencia_desde: val.fecha_vigencia_desde,
        fecha_vigencia_hasta: val.fecha_vigencia_hasta || '',
        es_version_activa: val.es_version_activa,
      })
    }
  },
  { immediate: true }
)

function handleSubmit() {
  emit('guardar', { ...form })
}
</script>
