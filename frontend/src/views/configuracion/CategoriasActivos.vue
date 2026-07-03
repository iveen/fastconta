<template>
  <div class="max-w-7xl mx-auto">
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">🏗️ Categorías de Activos Fijos</h1>
        <p class="text-sm text-gray-500">Tasas de depreciación según Decreto 10-2012</p>
      </div>
      <button @click="abrirModalCrear" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2">
        <PlusIcon class="w-4 h-4" />
        Nueva Categoría
      </button>
    </div>

    <div class="bg-white rounded-lg shadow-sm border p-4 mb-4 flex gap-3">
      <input v-model="filtros.search" type="text" placeholder="Buscar por nombre o prefijo..." class="flex-1 px-3 py-2 border rounded-lg text-sm" @input="debouncedCargar" />
      <select v-model="filtros.is_active" @change="cargar" class="px-3 py-2 border rounded-lg text-sm">
        <option :value="null">Todas</option>
        <option :value="true">Activas</option>
        <option :value="false">Inactivas</option>
      </select>
    </div>

    <div class="bg-white rounded-lg shadow-sm border overflow-hidden">
      <div v-if="loading" class="p-8 text-center text-gray-500">Cargando...</div>
      <table v-else class="w-full">
        <thead class="bg-gray-50 border-b">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Prefijo</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Nombre</th>
            <th class="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase">Tasa Mín.</th>
            <th class="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase">Tasa Máx.</th>
            <th class="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase">Vida útil (meses)</th>
            <th class="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase">Estado</th>
            <th class="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y">
          <tr v-for="c in categorias" :key="c.id" class="hover:bg-gray-50">
            <td class="px-4 py-3 text-sm font-mono font-semibold text-blue-600">{{ c.codigo_prefijo }}</td>
            <td class="px-4 py-3 text-sm font-medium">{{ c.nombre }}</td>
            <td class="px-4 py-3 text-sm text-center">{{ c.tasa_minima_anual }}%</td>
            <td class="px-4 py-3 text-sm text-center">{{ c.tasa_maxima_anual }}%</td>
            <td class="px-4 py-3 text-sm text-center">{{ c.vida_util_meses_default }}</td>
            <td class="px-4 py-3 text-center">
              <span :class="c.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-600'" class="px-2 py-1 rounded-full text-xs font-medium">
                {{ c.is_active ? 'Activa' : 'Inactiva' }}
              </span>
            </td>
            <td class="px-4 py-3 text-right space-x-2">
              <button @click="abrirModalEditar(c)" class="text-blue-600 hover:text-blue-800 text-sm">Editar</button>
              <button @click="toggleEstado(c)" :class="c.is_active ? 'text-red-600' : 'text-emerald-600'" class="text-sm">
                {{ c.is_active ? 'Desactivar' : 'Activar' }}
              </button>
            </td>
          </tr>
          <tr v-if="!categorias.length"><td colspan="7" class="px-4 py-8 text-center text-gray-500">No hay categorías registradas</td></tr>
        </tbody>
      </table>
    </div>

    <!-- Modal -->
    <div v-if="modal.abierto" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="cerrarModal">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
        <h2 class="text-xl font-bold mb-4">{{ modal.editando ? 'Editar Categoría' : 'Nueva Categoría' }}</h2>
        <form @submit.prevent="guardar" class="space-y-4">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Prefijo *</label>
              <input v-model="form.codigo_prefijo" type="text" required maxlength="10" :disabled="modal.editando" class="w-full px-3 py-2 border rounded-lg font-mono uppercase" placeholder="VEH" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Vida útil (meses) *</label>
              <input v-model.number="form.vida_util_meses_default" type="number" required min="1" class="w-full px-3 py-2 border rounded-lg" />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nombre *</label>
            <input v-model="form.nombre" type="text" required maxlength="100" class="w-full px-3 py-2 border rounded-lg" placeholder="Vehículos" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
            <textarea v-model="form.descripcion" rows="2" class="w-full px-3 py-2 border rounded-lg" placeholder="Vehículos de transporte terrestre"></textarea>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Tasa mínima anual (%) *</label>
              <input v-model="form.tasa_minima_anual" type="number" step="0.01" min="0" max="100" required class="w-full px-3 py-2 border rounded-lg" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Tasa máxima anual (%) *</label>
              <input v-model="form.tasa_maxima_anual" type="number" step="0.01" min="0" max="100" required class="w-full px-3 py-2 border rounded-lg" />
            </div>
          </div>
          <div class="flex items-center gap-2">
            <input v-model="form.is_active" type="checkbox" id="is_active" class="rounded" />
            <label for="is_active" class="text-sm">Activa</label>
          </div>
          <div v-if="error" class="text-sm text-red-600 bg-red-50 p-2 rounded">{{ error }}</div>
          <div class="flex justify-end gap-2 pt-2">
            <button type="button" @click="cerrarModal" class="px-4 py-2 border rounded-lg">Cancelar</button>
            <button type="submit" :disabled="guardando" class="px-4 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50">
              {{ guardando ? 'Guardando...' : 'Guardar' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Plus as PlusIcon } from '@lucide/vue'
import { useCategoriasActivosApi } from '@/composables/catalogos/useCategoriasActivosApi'
import { useToast } from '@/composables/useToast'

const { listar, crear, actualizar, eliminar } = useCategoriasActivosApi()
const toast = useToast()

const categorias = ref([])
const loading = ref(false)
const guardando = ref(false)
const error = ref(null)

const filtros = reactive({ search: '', is_active: null })
const modal = reactive({ abierto: false, editando: false, id: null })
const form = reactive({
  codigo_prefijo: '', nombre: '', descripcion: '',
  tasa_minima_anual: 0, tasa_maxima_anual: 0,
  vida_util_meses_default: 60, is_active: true
})

let debounceTimer = null
const debouncedCargar = () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(cargar, 300)
}

const cargar = async () => {
  loading.value = true
  try {
    const params = { skip: 0, limit: 200 }
    if (filtros.search) params.search = filtros.search
    if (filtros.is_active !== null) params.is_active = filtros.is_active
    const res = await listar(params)
    categorias.value = res.data
  } catch (e) {
    toast.error('Error al cargar categorías')
  } finally {
    loading.value = false
  }
}

const abrirModalCrear = () => {
  modal.abierto = true
  modal.editando = false
  Object.assign(form, {
    codigo_prefijo: '', nombre: '', descripcion: '',
    tasa_minima_anual: 0, tasa_maxima_anual: 0,
    vida_util_meses_default: 60, is_active: true
  })
  error.value = null
}

const abrirModalEditar = (c) => {
  modal.abierto = true
  modal.editando = true
  modal.id = c.id
  Object.assign(form, {
    codigo_prefijo: c.codigo_prefijo,
    nombre: c.nombre,
    descripcion: c.descripcion || '',
    tasa_minima_anual: Number(c.tasa_minima_anual),
    tasa_maxima_anual: Number(c.tasa_maxima_anual),
    vida_util_meses_default: c.vida_util_meses_default,
    is_active: c.is_active
  })
  error.value = null
}

const cerrarModal = () => { modal.abierto = false }

const guardar = async () => {
  if (Number(form.tasa_maxima_anual) < Number(form.tasa_minima_anual)) {
    error.value = 'La tasa máxima debe ser mayor o igual a la mínima'
    return
  }
  guardando.value = true
  error.value = null
  try {
    if (modal.editando) {
      await actualizar(modal.id, { ...form })
      toast.success('Categoría actualizada')
    } else {
      await crear({ ...form })
      toast.success('Categoría creada')
    }
    cerrarModal()
    await cargar()
  } catch (e) {
    error.value = e.response?.data?.detail || 'Error al guardar'
  } finally {
    guardando.value = false
  }
}

const toggleEstado = async (c) => {
  try {
    await eliminar(c.id)
    toast.success(c.is_active ? 'Categoría desactivada' : 'Categoría activada')
    await cargar()
  } catch (e) {
    toast.error('Error al actualizar estado')
  }
}

onMounted(cargar)
</script>