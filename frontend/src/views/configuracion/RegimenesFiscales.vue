<!-- src/views/configuracion/RegimenesFiscales.vue -->
<template>
  <div class="max-w-7xl mx-auto">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">Regímenes Fiscales</h1>
        <p class="text-sm text-gray-500">Administra los regímenes tributarios disponibles</p>
      </div>
      <button
        @click="abrirModalCrear"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
      >
        <PlusIcon class="w-4 h-4" />
        Nuevo Régimen
      </button>
    </div>

    <!-- Filtros -->
    <div class="bg-white rounded-lg shadow-sm border p-4 mb-4 flex gap-3">
      <input
        v-model="filtros.search"
        type="text"
        placeholder="Buscar por código, nombre..."
        class="flex-1 px-3 py-2 border rounded-lg text-sm"
        @input="debouncedCargar"
      />
      <select v-model="filtros.is_active" @change="cargar" class="px-3 py-2 border rounded-lg text-sm">
        <option :value="null">Todos los estados</option>
        <option :value="true">Activos</option>
        <option :value="false">Inactivos</option>
      </select>
    </div>

    <!-- Tabla -->
    <div class="bg-white rounded-lg shadow-sm border overflow-hidden">
      <div v-if="loading" class="p-8 text-center text-gray-500">Cargando...</div>
      <table v-else class="w-full">
        <thead class="bg-gray-50 border-b">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Código</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Nombre</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Descripción</th>
            <th class="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase">Estado</th>
            <th class="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y">
          <tr v-for="regimen in regimenes" :key="regimen.id" class="hover:bg-gray-50">
            <td class="px-4 py-3 text-sm font-mono text-blue-600">{{ regimen.codigo }}</td>
            <td class="px-4 py-3 text-sm font-medium">{{ regimen.nombre }}</td>
            <td class="px-4 py-3 text-sm text-gray-600 max-w-xs truncate">{{ regimen.descripcion || '—' }}</td>
            <td class="px-4 py-3 text-center">
              <span
                :class="regimen.is_active
                  ? 'bg-emerald-100 text-emerald-700'
                  : 'bg-gray-100 text-gray-600'"
                class="px-2 py-1 rounded-full text-xs font-medium"
              >
                {{ regimen.is_active ? 'Activo' : 'Inactivo' }}
              </span>
            </td>
            <td class="px-4 py-3 text-right space-x-2">
              <button
                @click="abrirModalEditar(regimen)"
                class="text-blue-600 hover:text-blue-800 text-sm"
              >Editar</button>
              <button
                @click="confirmarEliminar(regimen)"
                :class="regimen.is_active ? 'text-red-600 hover:text-red-800' : 'text-emerald-600 hover:text-emerald-800'"
                class="text-sm"
              >
                {{ regimen.is_active ? 'Desactivar' : 'Activar' }}
              </button>
            </td>
          </tr>
          <tr v-if="!regimenes.length">
            <td colspan="5" class="px-4 py-8 text-center text-gray-500">
              No hay regímenes registrados
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal Crear/Editar -->
    <div
      v-if="modal.abierto"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="cerrarModal"
    >
      <div class="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
        <h2 class="text-xl font-bold mb-4">
          {{ modal.editando ? 'Editar Régimen' : 'Nuevo Régimen' }}
        </h2>
        <form @submit.prevent="guardar" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Código *</label>
            <input
              v-model="form.codigo"
              type="text"
              required
              :disabled="modal.editando"
              class="w-full px-3 py-2 border rounded-lg"
              placeholder="Ej: PC_FEL"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nombre *</label>
            <input
              v-model="form.nombre"
              type="text"
              required
              class="w-full px-3 py-2 border rounded-lg"
              placeholder="Ej: Pequeño Contribuyente Electrónico"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
            <textarea
              v-model="form.descripcion"
              rows="3"
              class="w-full px-3 py-2 border rounded-lg"
              placeholder="Base legal, tasa, frecuencia..."
            ></textarea>
          </div>
          <div class="flex items-center gap-2">
            <input v-model="form.is_active" type="checkbox" id="is_active" class="rounded" />
            <label for="is_active" class="text-sm">Activo</label>
          </div>
          <div v-if="error" class="text-sm text-red-600 bg-red-50 p-2 rounded">{{ error }}</div>
          <div class="flex justify-end gap-2 pt-2">
            <button
              type="button"
              @click="cerrarModal"
              class="px-4 py-2 border rounded-lg hover:bg-gray-50"
            >Cancelar</button>
            <button
              type="submit"
              :disabled="guardando"
              class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {{ guardando ? 'Guardando...' : 'Guardar' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal Confirmación Eliminar -->
    <div
      v-if="confirmar.abierto"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
    >
      <div class="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <h3 class="text-lg font-bold mb-2">
          {{ confirmar.item.is_active ? '¿Desactivar régimen?' : '¿Activar régimen?' }}
        </h3>
        <p class="text-sm text-gray-600 mb-4">
          <strong>{{ confirmar.item.codigo }}</strong> - {{ confirmar.item.nombre }}
        </p>
        <div class="flex justify-end gap-2">
          <button @click="confirmar.abierto = false" class="px-4 py-2 border rounded-lg">Cancelar</button>
          <button
            @click="ejecutarEliminar"
            :class="confirmar.item.is_active ? 'bg-red-600 hover:bg-red-700' : 'bg-emerald-600 hover:bg-emerald-700'"
            class="px-4 py-2 text-white rounded-lg"
          >Confirmar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Plus as PlusIcon } from '@lucide/vue'
import { useRegimenesApi } from '@/composables/configuracion/useRegimenesApi'
import { useToast } from '@/composables/useToast'

const { listar, crear, actualizar, eliminar } = useRegimenesApi()
const toast = useToast()

const regimenes = ref([])
const loading = ref(false)
const guardando = ref(false)
const error = ref(null)

const filtros = reactive({
  search: '',
  is_active: null
})

const modal = reactive({
  abierto: false,
  editando: false,
  id: null
})

const form = reactive({
  codigo: '',
  nombre: '',
  descripcion: '',
  is_active: true
})

const confirmar = reactive({
  abierto: false,
  item: null
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
    regimenes.value = res.data
  } catch (e) {
    toast.error('Error al cargar regímenes')
  } finally {
    loading.value = false
  }
}

const abrirModalCrear = () => {
  modal.abierto = true
  modal.editando = false
  modal.id = null
  form.codigo = ''
  form.nombre = ''
  form.descripcion = ''
  form.is_active = true
  error.value = null
}

const abrirModalEditar = (regimen) => {
  modal.abierto = true
  modal.editando = true
  modal.id = regimen.id
  form.codigo = regimen.codigo
  form.nombre = regimen.nombre
  form.descripcion = regimen.descripcion || ''
  form.is_active = regimen.is_active
  error.value = null
}

const cerrarModal = () => {
  modal.abierto = false
}

const guardar = async () => {
  guardando.value = true
  error.value = null
  try {
    const payload = { ...form }
    if (modal.editando) {
      await actualizar(modal.id, payload)
      toast.success('Régimen actualizado')
    } else {
      await crear(payload)
      toast.success('Régimen creado')
    }
    cerrarModal()
    await cargar()
  } catch (e) {
    error.value = e.response?.data?.detail || 'Error al guardar'
  } finally {
    guardando.value = false
  }
}

const confirmarEliminar = (regimen) => {
  confirmar.item = regimen
  confirmar.abierto = true
}

const ejecutarEliminar = async () => {
  try {
    await eliminar(confirmar.item.id)
    toast.success(confirmar.item.is_active ? 'Régimen desactivado' : 'Régimen activado')
    confirmar.abierto = false
    await cargar()
  } catch (e) {
    toast.error('Error al actualizar estado')
  }
}

onMounted(cargar)
</script>