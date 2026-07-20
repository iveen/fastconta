<!-- src/components/inventarios/ModalBodega.vue -->
<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
    <div class="bg-white rounded-xl shadow-2xl w-full max-w-md p-6">
      <h3 class="text-lg font-bold text-gray-900 mb-4">
        {{ bodega ? 'Editar Bodega' : 'Nueva Bodega' }}
      </h3>

      <form @submit.prevent="guardar" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Código *</label>
          <input v-model="form.codigo" type="text" required maxlength="20" class="w-full px-3 py-2 border border-gray-300 rounded-md" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Nombre *</label>
          <input v-model="form.nombre" type="text" required maxlength="100" class="w-full px-3 py-2 border border-gray-300 rounded-md" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Ubicación</label>
          <input v-model="form.ubicacion" type="text" maxlength="200" class="w-full px-3 py-2 border border-gray-300 rounded-md" />
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
  bodega: { type: Object, default: null }
})
const emit = defineEmits(['close', 'guardado'])

const form = ref({ codigo: '', nombre: '', ubicacion: '' })
const cargando = ref(false)
const error = ref(null)

onMounted(() => {
  if (props.bodega) {
    form.value = {
      codigo: props.bodega.codigo,
      nombre: props.bodega.nombre,
      ubicacion: props.bodega.ubicacion || ''
    }
  }
})

async function guardar() {
  cargando.value = true
  error.value = null
  try {
    if (props.bodega) {
      await inventarioService.actualizarBodega(props.bodega.public_id, form.value)
      toast.success('Bodega actualizada')
    } else {
      await inventarioService.crearBodega(props.empresaPublicId, form.value)
      toast.success('Bodega creada')
    }
    emit('guardado')
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al guardar'
  } finally {
    cargando.value = false
  }
}
</script>