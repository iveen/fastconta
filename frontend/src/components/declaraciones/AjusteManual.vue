<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl max-w-md w-full">
      <div class="px-6 py-4 border-b">
        <h3 class="font-bold text-lg">Ajuste Manual</h3>
        <p class="text-sm text-gray-600 mt-1">{{ casilla.casilla_nombre }}</p>
      </div>

      <form @submit.prevent="guardar" class="p-6 space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Base Imponible (Q)</label>
          <input v-model.number="form.base" type="number" step="0.01" class="w-full border rounded px-3 py-2" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Monto Impuesto (Q)</label>
          <input v-model.number="form.impuesto" type="number" step="0.01" class="w-full border rounded px-3 py-2" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Motivo del Ajuste <span class="text-red-500">*</span>
          </label>
          <textarea
            v-model="form.motivo"
            required
            rows="3"
            class="w-full border rounded px-3 py-2"
            placeholder="Ej: Factura mal clasificada por el sistema, se reclasifica según..."
          ></textarea>
          <p class="text-xs text-gray-500 mt-1">
            Este motivo quedará registrado en la auditoría. Mínimo 5 caracteres.
          </p>
        </div>

        <div class="flex gap-2 justify-end pt-2">
          <button type="button" @click="$emit('close')" class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded">
            Cancelar
          </button>
          <button
            type="submit"
            :disabled="guardando || form.motivo.length < 5"
            class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
          >
            {{ guardando ? 'Guardando...' : 'Aplicar Ajuste' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { declaracionesApi } from '@/services/declaraciones' 

const props = defineProps({
  declaracionId: { type: String, required: true },
  casilla: { type: Object, required: true },
})
const emit = defineEmits(['close', 'guardado'])

const form = reactive({
  base: props.casilla.base_imponible,
  impuesto: props.casilla.monto_impuesto,
  motivo: props.casilla.motivo_ajuste || '',
})
const guardando = ref(false)

const guardar = async () => {
  guardando.value = true
  try {
    await declaracionesApi.aplicarAjuste(props.declaracionId, props.casilla.casilla_codigo, {
      base_imponible: form.base,
      monto_impuesto: form.impuesto,
      motivo_ajuste: form.motivo,
    })
    emit('guardado')
    emit('close')
  } catch (e) {
    alert('Error: ' + e.message)
  } finally {
    guardando.value = false
  }
}
</script>