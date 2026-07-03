<!-- src/views/configuracion/RegimenDTE.vue -->
<template>
  <div class="max-w-7xl mx-auto">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800">Configuración Régimen-DTE</h1>
      <p class="text-sm text-gray-500">Define qué tipos DTE puede emitir cada régimen fiscal</p>
    </div>

    <!-- Selector de Régimen -->
    <div class="bg-white rounded-lg shadow-sm border p-4 mb-6">
      <label class="block text-sm font-medium text-gray-700 mb-2">Selecciona un régimen fiscal</label>
      <select
        v-model="regimenSeleccionadoId"
        @change="cargarConfiguracion"
        class="w-full px-3 py-2 border rounded-lg"
      >
        <option :value="null" disabled>-- Selecciona un régimen --</option>
        <option v-for="r in regimenes" :key="r.id" :value="r.id">
          {{ r.codigo }} - {{ r.nombre }}
        </option>
      </select>
    </div>

    <div v-if="regimenSeleccionadoId" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Columna izquierda: DTE asociados -->
      <div class="bg-white rounded-lg shadow-sm border">
        <div class="p-4 border-b flex justify-between items-center">
          <h2 class="font-semibold text-gray-800">DTE configurados ({{ configs.length }})</h2>
          <button
            @click="abrirModalAsociar"
            class="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 flex items-center gap-1"
          >
            <PlusIcon class="w-4 h-4" />
            Asociar DTE
          </button>
        </div>
        <div v-if="loading" class="p-8 text-center text-gray-500">Cargando...</div>
        <div v-else-if="!configs.length" class="p-8 text-center text-gray-500">
          No hay DTE configurados para este régimen
        </div>
        <ul v-else class="divide-y">
          <li v-for="c in configs" :key="c.id" class="p-4 flex items-center justify-between hover:bg-gray-50">
            <div>
              <p class="font-mono text-sm text-blue-600">{{ c.dte_codigo }}</p>
              <p class="text-sm text-gray-700">{{ c.dte_descripcion }}</p>
              <p v-if="c.es_exclusivo" class="text-xs text-amber-600 mt-1">⚠️ Exclusivo</p>
            </div>
            <div class="flex gap-2">
              <button
                @click="toggleExclusivo(c)"
                class="text-xs px-2 py-1 border rounded hover:bg-gray-50"
              >
                {{ c.es_exclusivo ? 'Quitar exclusivo' : 'Marcar exclusivo' }}
              </button>
              <button
                @click="confirmarDesasociar(c)"
                class="text-xs px-2 py-1 text-red-600 border rounded hover:bg-red-50"
              >Desasociar</button>
            </div>
          </li>
        </ul>
      </div>

      <!-- Columna derecha: Todos los DTE disponibles -->
      <div class="bg-white rounded-lg shadow-sm border">
        <div class="p-4 border-b">
          <h2 class="font-semibold text-gray-800">Todos los tipos DTE</h2>
          <p class="text-xs text-gray-500">Los marcados ya están asociados</p>
        </div>
        <ul class="divide-y max-h-150 overflow-y-auto">
          <li
            v-for="dte in todosDTE"
            :key="dte.id"
            class="p-3 flex items-center gap-3 hover:bg-gray-50"
          >
            <input
              type="checkbox"
              :checked="estaAsociado(dte.id)"
              @change="toggleAsociacion(dte)"
              :disabled="dteToggleando[dte.id]"
              class="rounded"
            />
            <div class="flex-1">
              <p class="font-mono text-sm text-blue-600">{{ dte.codigo }}</p>
              <p class="text-sm text-gray-700">{{ dte.descripcion }}</p>
            </div>
            <span v-if="estaAsociado(dte.id)" class="text-xs text-emerald-600">✓ Asociado</span>
          </li>
        </ul>
      </div>
    </div>

    <div v-else class="bg-amber-50 border border-amber-200 rounded-lg p-6 text-center text-amber-800">
      Selecciona un régimen para ver su configuración de DTE
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { Plus as PlusIcon } from '@lucide/vue'
import { useRegimenesApi } from '@/composables/configuracion/useRegimenesApi'
import { useTiposDTEApi } from '@/composables/configuracion/useTiposDTEApi'
import { useRegimenDTEApi } from '@/composables/configuracion/useRegimenDTEApi'
import { useToast } from '@/composables/useToast'

const { listarActivos: listarRegimenes } = useRegimenesApi()
const { listarActivos: listarDTE } = useTiposDTEApi()
const { listarPorRegimen, asociar, actualizar, desasociar } = useRegimenDTEApi()
const toast = useToast()

const regimenes = ref([])
const todosDTE = ref([])
const configs = ref([])
const regimenSeleccionadoId = ref(null)
const loading = ref(false)
const dteToggleando = reactive({})

const cargarCatalogos = async () => {
  const [regs, dtes] = await Promise.all([listarRegimenes(), listarDTE()])
  regimenes.value = regs
  todosDTE.value = dtes
}

const cargarConfiguracion = async () => {
  if (!regimenSeleccionadoId.value) return
  loading.value = true
  try {
    configs.value = await listarPorRegimen(regimenSeleccionadoId.value)
  } catch (e) {
    toast.error('Error al cargar configuración')
  } finally {
    loading.value = false
  }
}

const estaAsociado = (dteId) => configs.value.some(c => c.dte_id === dteId)

const toggleAsociacion = async (dte) => {
  const yaExiste = estaAsociado(dte.id)
  dteToggleando[dte.id] = true
  try {
    if (yaExiste) {
      await desasociar(regimenSeleccionadoId.value, dte.id)
      toast.success('DTE desasociado')
    } else {
      await asociar(regimenSeleccionadoId.value, {
        regimen_id: regimenSeleccionadoId.value,
        dte_id: dte.id,
        es_exclusivo: false
      })
      toast.success('DTE asociado')
    }
    await cargarConfiguracion()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Error al actualizar')
  } finally {
    dteToggleando[dte.id] = false
  }
}

const toggleExclusivo = async (config) => {
  try {
    await actualizar(
      regimenSeleccionadoId.value,
      config.dte_id,
      { es_exclusivo: !config.es_exclusivo }
    )
    toast.success('Configuración actualizada')
    await cargarConfiguracion()
  } catch (e) {
    toast.error('Error al actualizar')
  }
}

const confirmarDesasociar = async (config) => {
  if (!confirm(`¿Desasociar ${config.dte_codigo}?`)) return
  try {
    await desasociar(regimenSeleccionadoId.value, config.dte_id)
    toast.success('DTE desasociado')
    await cargarConfiguracion()
  } catch (e) {
    toast.error('Error al desasociar')
  }
}

const abrirModalAsociar = () => {
  // Scroll al panel derecho para que el usuario vea los DTE disponibles
  window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })
}

onMounted(cargarCatalogos)
</script>