<template>
  <div class="max-w-7xl mx-auto">
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">💼 Actividades Económicas</h1>
        <p class="text-sm text-gray-500">Catálogo SAT de actividades económicas</p>
      </div>
      <button v-if="authStore.isSuperAdmin" @click="abrirModalCrear" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2">
        <PlusIcon class="w-4 h-4" />
        Nueva Actividad
      </button>
    </div>

    <div class="bg-white rounded-lg shadow-sm border p-4 mb-4 flex gap-3">
      <input v-model="filtros.search" type="text" placeholder="Buscar por código o nombre..." class="flex-1 px-3 py-2 border rounded-lg text-sm" @input="debouncedCargar" />
      <select v-model="filtros.activa" @change="cargar" class="px-3 py-2 border rounded-lg text-sm">
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
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase w-32">Código SAT</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Nombre</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase w-64">Sección</th>
            <th class="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase w-24">Estado</th>
            <th class="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase w-40">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y">
          <tr v-for="a in actividades" :key="a.id" class="hover:bg-gray-50">
            <td class="px-4 py-3 text-sm font-mono text-blue-600">{{ a.codigo_sat }}</td>
            <td class="px-4 py-3 text-sm">{{ a.nombre_actividad }}</td>
            <td class="px-4 py-3 text-sm text-gray-600">{{ a.seccion || '—' }}</td>
            <td class="px-4 py-3 text-center">
              <span :class="a.activa ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-600'" class="px-2 py-1 rounded-full text-xs font-medium">
                {{ a.activa ? 'Activa' : 'Inactiva' }}
              </span>
            </td>
            <td v-if="authStore.isSuperAdmin" class="px-4 py-3 text-right space-x-2">
              <button @click="abrirModalEditar(a)" class="text-blue-600 hover:text-blue-800 text-sm">Editar</button>
              <button @click="toggleEstado(a)" :class="a.activa ? 'text-red-600' : 'text-emerald-600'" class="text-sm">
                {{ a.activa ? 'Desactivar' : 'Activar' }}
              </button>
            </td>
          </tr>
          <tr v-if="!actividades.length"><td colspan="5" class="px-4 py-8 text-center text-gray-500">No hay actividades registradas</td></tr>
        </tbody>
      </table>
    </div>

    <!-- Modal -->
    <div v-if="modal.abierto" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="cerrarModal">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
        <h2 class="text-xl font-bold mb-4">{{ modal.editando ? 'Editar Actividad' : 'Nueva Actividad' }}</h2>
        <form @submit.prevent="guardar" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Código SAT *</label>
            <input v-model="form.codigo_sat" type="text" required maxlength="20" :disabled="modal.editando" class="w-full px-3 py-2 border rounded-lg font-mono" placeholder="01101" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nombre *</label>
            <input v-model="form.nombre_actividad" type="text" required maxlength="255" class="w-full px-3 py-2 border rounded-lg" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Sección</label>
            <input v-model="form.seccion" type="text" maxlength="255" class="w-full px-3 py-2 border rounded-lg" placeholder="A. Agricultura, ganadería..." />
          </div>
          <div class="flex items-center gap-2">
            <input v-model="form.activa" type="checkbox" id="activa" class="rounded" />
            <label for="activa" class="text-sm">Activa</label>
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
import { useActividadesApi } from '@/composables/catalogos/useActividadesApi'
import { useToast } from '@/composables/useToast'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const { listar, crear, actualizar, eliminar } = useActividadesApi()
const toast = useToast()

const actividades = ref([])
const loading = ref(false)
const guardando = ref(false)
const error = ref(null)

const filtros = reactive({ search: '', activa: null })
const modal = reactive({ abierto: false, editando: false, id: null })
const form = reactive({ codigo_sat: '', nombre_actividad: '', seccion: '', activa: true })

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
    if (filtros.activa !== null) params.activa = filtros.activa
    const res = await listar(params)
    actividades.value = res.data
  } catch (e) {
    toast.error('Error al cargar actividades')
  } finally {
    loading.value = false
  }
}

const abrirModalCrear = () => {
  modal.abierto = true
  modal.editando = false
  Object.assign(form, { codigo_sat: '', nombre_actividad: '', seccion: '', activa: true })
  error.value = null
}

const abrirModalEditar = (a) => {
  modal.abierto = true
  modal.editando = true
  modal.id = a.id
  Object.assign(form, {
    codigo_sat: a.codigo_sat,
    nombre_actividad: a.nombre_actividad,
    seccion: a.seccion || '',
    activa: a.activa
  })
  error.value = null
}

const cerrarModal = () => { modal.abierto = false }

const guardar = async () => {
  guardando.value = true
  error.value = null
  try {
    if (modal.editando) {
      await actualizar(modal.id, { ...form })
      toast.success('Actividad actualizada')
    } else {
      await crear({ ...form })
      toast.success('Actividad creada')
    }
    cerrarModal()
    await cargar()
  } catch (e) {
    error.value = e.response?.data?.detail || 'Error al guardar'
  } finally {
    guardando.value = false
  }
}

const toggleEstado = async (a) => {
  try {
    await eliminar(a.id)
    toast.success(a.activa ? 'Actividad desactivada' : 'Actividad activada')
    await cargar()
  } catch (e) {
    toast.error('Error al actualizar estado')
  }
}

onMounted(cargar)
</script>