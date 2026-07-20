<!-- src/components/inventarios/ModalProducto.vue -->
<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
    <div class="bg-white rounded-xl shadow-2xl w-full max-w-md p-6">
      <h3 class="text-lg font-bold text-gray-900 mb-4">
        {{ producto ? 'Editar Producto' : 'Nuevo Producto' }}
      </h3>

      <form @submit.prevent="guardar" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Código (opcional)</label>
          <input v-model="form.codigo" type="text" maxlength="50" class="w-full px-3 py-2 border border-gray-300 rounded-md" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Descripción *</label>
          <input v-model="form.descripcion" type="text" required maxlength="255" class="w-full px-3 py-2 border border-gray-300 rounded-md" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Unidad de Medida *</label>
          <input v-model="form.unidad_medida" type="text" required maxlength="20" class="w-full px-3 py-2 border border-gray-300 rounded-md" />
          <p class="mt-1 text-xs text-gray-500">Ej: UND, KG, LT, CJ</p>
        </div>

        <p v-if="error" class="text-sm text-red-600 bg-red-50 p-3 rounded-md">{{ error }}</p>

        <div class="flex justify-end gap-3 pt-4 border-t">
          <button type="button" @click="$emit('close')" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">
            Cancelar
          </button>
          <button type="submit" :disabled="cargando" class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50">
            {{ cargando ? 'Guardando...' : 'Guardar' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { inventarioService } from '@/services/inventarioService'
import { toast } from 'vue3-toastify'

const props = defineProps({
  empresaPublicId: { type: String, required: true },
  producto: { type: Object, default: null }
})
const emit = defineEmits(['close', 'guardado'])

const form = ref({ codigo: '', descripcion: '', unidad_medida: 'UND' })
const cargando = ref(false)
const error = ref(null)

onMounted(() => {
  if (props.producto) {
    form.value = {
      codigo: props.producto.codigo || '',
      descripcion: props.producto.descripcion,
      unidad_medida: props.producto.unidad_medida || 'UND'
    }
  }
})

async function guardar() {
  cargando.value = true
  error.value = null
  try {
    if (props.producto) {
      await inventarioService.actualizarProducto(props.producto.public_id, form.value)
      toast.success('Producto actualizado')
    } else {
      await inventarioService.crearProducto(props.empresaPublicId, form.value)
      toast.success('Producto creado')
    }
    emit('guardado')
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al guardar'
  } finally {
    cargando.value = false
  }
}
</script>