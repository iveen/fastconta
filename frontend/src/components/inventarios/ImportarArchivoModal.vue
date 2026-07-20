<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
    <div class="bg-white rounded-xl shadow-2xl w-full max-w-xl p-6">
      <h3 class="text-lg font-bold text-gray-900 mb-4">Importar Inventario desde Archivo</h3>
      
      <div class="space-y-4">
        <!-- Modo -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Modo de importación</label>
          <select v-model="modo" class="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
            <option value="REEMPLAZAR">Reemplazar items existentes (Borra los actuales)</option>
            <option value="AGREGAR">Agregar a los existentes (Conserva los actuales)</option>
          </select>
        </div>

        <!-- Archivo -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Archivo Excel o CSV</label>
          <input 
            type="file" 
            @change="onFileChange" 
            accept=".xlsx,.xls,.csv"
            class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          />
          <p class="mt-1 text-xs text-gray-500">Máximo 100MB. Formatos: .xlsx, .xls, .csv</p>
        </div>

        <!-- Info de columnas -->
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">
          <p class="font-semibold mb-1">📋 Columnas esperadas:</p>
          <ul class="list-disc list-inside space-y-1 text-xs">
            <li><strong>Obligatorias:</strong> descripcion, costo_unitario, cantidad</li>
            <li><strong>Opcionales:</strong> codigo, unidad_medida, bodega</li>
          </ul>
        </div>

        <p v-if="error" class="text-sm text-red-600 bg-red-50 p-3 rounded-lg">{{ error }}</p>
      </div>

      <div class="mt-6 flex justify-end gap-3">
        <button @click="$emit('close')" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
          Cancelar
        </button>
        <button 
          @click="importar" 
          :disabled="!archivo || cargando"
          class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ cargando ? 'Iniciando...' : 'Iniciar Importación' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useInventarioStore } from '@/stores/inventarioStore'

const props = defineProps({ tomaPublicId: { type: String, required: true } })
const emit = defineEmits(['close', 'importacion-iniciada'])

const store = useInventarioStore()
const modo = ref('REEMPLAZAR')
const archivo = ref(null)
const cargando = ref(false)
const error = ref(null)

const onFileChange = (e) => {
  archivo.value = e.target.files[0]
  error.value = null
}

const importar = async () => {
  if (!archivo.value) {
    error.value = 'Por favor selecciona un archivo'
    return
  }
  if (archivo.value.size > 100 * 1024 * 1024) {
    error.value = 'El archivo excede el límite de 100MB'
    return
  }

  cargando.value = true
  try {
    const job = await store.iniciarImportacion(props.tomaPublicId, archivo.value, modo.value)
    emit('importacion-iniciada', job)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al iniciar la importación'
  } finally {
    cargando.value = false
  }
}
</script>