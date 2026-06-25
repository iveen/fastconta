<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-xl shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
      <!-- Header -->
      <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center sticky top-0 bg-white rounded-t-xl">
        <div>
          <h2 class="text-xl font-bold text-gray-800">{{ titulo }}</h2>
          <p class="text-sm text-gray-600 mt-1">
            Sección {{ seccionNumero }} - {{ seccionTitulo }}
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
              Código <span class="text-red-500">*</span>
            </label>
            <input
              v-model="form.codigo"
              type="text"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Ej: 3.1"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Código Visual
            </label>
            <input
              v-model="form.codigo_visual"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Ej: 3.1"
            />
          </div>
        </div>

        <div class="border-t border-gray-200 pt-4">
          <h3 class="text-sm font-semibold text-gray-700 mb-3">Orden y Visualización</h3>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Orden en la Sección
            </label>
            <input
              v-model.number="form.orden_seccion"
              type="number"
              min="0"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="0"
            />
            <p class="text-xs text-gray-500 mt-1">
              Las casillas se mostrarán ordenadas de menor a mayor
            </p>
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
            placeholder="Nombre de la casilla"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
          <textarea
            v-model="form.descripcion"
            rows="2"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Descripción de la casilla"
          ></textarea>
        </div>

        <!-- Configuración -->
        <div class="border-t border-gray-200 pt-4">
          <h3 class="text-sm font-semibold text-gray-700 mb-3">Configuración</h3>
          
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Tipo de Casilla <span class="text-red-500">*</span>
              </label>
              <select
                v-model="form.tipo_casilla"
                required
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Seleccione...</option>
                <option value="BASE_IMPONIBLE">Base Imponible</option>
                <option value="DEBITO_FISCAL">Débito Fiscal</option>
                <option value="CREDITO_FISCAL">Crédito Fiscal</option>
                <option value="REFERENCIA">Referencia</option>
                <option value="CALCULADO">Calculado</option>
                <option value="REMANENTE">Remanente</option>
                <option value="AJUSTE">Ajuste</option>
                <option value="CONTEO">Conteo</option>
                <option value="MANUAL">Manual</option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Naturaleza
              </label>
              <select
                v-model="form.naturaleza"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Seleccione...</option>
                <option value="SUMA">Suma</option>
                <option value="RESTA">Resta</option>
                <option value="PORCENTAJE">Porcentaje</option>
                <option value="MANUAL">Manual</option>
                <option value="CONTEO">Conteo</option>
              </select>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4 mt-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Campo Origen Factura
              </label>
              <input
                v-model="form.campo_origen_factura"
                type="text"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Ej: total_gravado_gtq"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Fórmula de Cálculo
              </label>
              <input
                v-model="form.formula_calculo"
                type="text"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Ej: campo1 * 0.12"
              />
            </div>
          </div>

          <div class="mt-4">
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Porcentaje Aplicable (%)
            </label>
            <input
              v-model.number="form.porcentaje_aplicable"
              type="number"
              step="0.01"
              min="0"
              max="100"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Ej: 12.00"
            />
          </div>
        </div>

        <!-- Banderas -->
        <div class="border-t border-gray-200 pt-4">
          <h3 class="text-sm font-semibold text-gray-700 mb-3">Opciones</h3>
          
          <div class="space-y-2">
            <label class="flex items-center">
              <input
                v-model="form.es_editable"
                type="checkbox"
                class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span class="ml-2 text-sm text-gray-700">Editable por el usuario</span>
            </label>

            <label class="flex items-center">
              <input
                v-model="form.requiere_justificacion"
                type="checkbox"
                class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span class="ml-2 text-sm text-gray-700">Requiere justificación</span>
            </label>

            <label class="flex items-center">
              <input
                v-model="form.es_visible_usuario"
                type="checkbox"
                class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                checked
              />
              <span class="ml-2 text-sm text-gray-700">Visible para el usuario</span>
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
  loading: { type: Boolean, default: false },
  seccionId: { type: String, default: null },  // ✅ NUEVO
  seccionNumero: { type: String, default: '' },
  seccionTitulo: { type: String, default: '' },
  siguienteOrden: { type: Number, default: 0 },
})

const emit = defineEmits(['cancelar', 'guardar'])

const form = reactive({
  codigo: '',
  codigo_visual: '',
  nombre: '',
  descripcion: '',
  tipo_casilla: '',
  naturaleza: '',
  campo_origen_factura: '',
  formula_calculo: '',
  porcentaje_aplicable: null,
  orden_seccion: 0,
  es_editable: false,
  requiere_justificacion: false,
  es_visible_usuario: true,
})

watch(
  () => props.data,
  (val) => {
    if (val) {
      Object.assign(form, {
        codigo: val.codigo || '',
        codigo_visual: val.codigo_visual || '',
        nombre: val.nombre || '',
        descripcion: val.descripcion || '',
        tipo_casilla: val.tipo_casilla || '',
        naturaleza: val.naturaleza || '',
        campo_origen_factura: val.campo_origen_factura || '',
        formula_calculo: val.formula_calculo || '',
        porcentaje_aplicable: val.porcentaje_aplicable,
        orden_seccion: val.orden_seccion || 0,
        es_editable: val.es_editable || false,
        requiere_justificacion: val.requiere_justificacion || false,
        es_visible_usuario: val.es_visible_usuario !== undefined ? val.es_visible_usuario : true,
      })
    }
  },
  { immediate: true }
)

function handleSubmit() {
  const payload = { 
    ...form,
    seccion_id: props.seccionId  // ✅ Incluir seccion_id
  }
  console.log('📤 Payload a enviar:', payload)
  console.log('📋 seccionId prop:', props.seccionId)
  emit('guardar', payload)
}
</script>