<template>
  <div class="max-w-4xl mx-auto">
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">👤 Tipos de Persona</h1>
        <p class="text-sm text-gray-500">Catálogo de tipos de persona (Natural, Jurídica, etc.)</p>
      </div>
      <button v-if="authStore.isSuperAdmin" @click="abrirModalCrear" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2">
        <PlusIcon class="w-4 h-4" />
        Nuevo Tipo
      </button>
    </div>

    <div class="bg-white rounded-lg shadow-sm border overflow-hidden">
      <div v-if="loading" class="p-8 text-center text-gray-500">Cargando...</div>
      <table v-else class="w-full">
        <thead class="bg-gray-50 border-b">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Nombre</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Descripción</th>
            <th class="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y">
          <tr v-for="t in tipos" :key="t.id" class="hover:bg-gray-50">
            <td class="px-4 py-3 text-sm font-mono font-semibold text-blue-600">{{ t.nombre }}</td>
            <td class="px-4 py-3 text-sm text-gray-600">{{ t.descripcion || '—' }}</td>
            <td v-if="authStore.isSuperAdmin" class="px-4 py-3 text-right space-x-2">
              <button @click="abrirModalEditar(t)" class="text-blue-600 hover:text-blue-800 text-sm">Editar</button>
              <button @click="confirmarEliminar(t)" class="text-red-600 hover:text-red-800 text-sm">Eliminar</button>
            </td>
          </tr>
          <tr v-if="!tipos.length"><td colspan="3" class="px-4 py-8 text-center text-gray-500">No hay tipos de persona registrados</td></tr>
        </tbody>
      </table>
    </div>

    <!-- Modal -->
    <div v-if="modal.abierto" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="cerrarModal">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <h2 class="text-xl font-bold mb-4">{{ modal.editando ? 'Editar Tipo' : 'Nuevo Tipo de Persona' }}</h2>
        <form @submit.prevent="guardar" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nombre *</label>
            <input v-model="form.nombre" type="text" required maxlength="50" :disabled="modal.editando" class="w-full px-3 py-2 border rounded-lg font-mono uppercase" placeholder="NATURAL" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
            <textarea v-model="form.descripcion" rows="3" maxlength="200" class="w-full px-3 py-2 border rounded-lg" placeholder="Persona individual según Art. 72 LIR"></textarea>
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
import { useTiposPersonaApi } from '@/composables/catalogos/useTiposPersonaApi'
import { useToast } from '@/composables/useToast'
import { useAuthStore } from '@/stores/auth'
const authStore = useAuthStore()   

const { listar, crear, actualizar, eliminar } = useTiposPersonaApi()
const toast = useToast()

const tipos = ref([])
const loading = ref(false)
const guardando = ref(false)
const error = ref(null)

const modal = reactive({ abierto: false, editando: false, id: null })
const form = reactive({ nombre: '', descripcion: '' })

const cargar = async () => {
  loading.value = true
  try {
    tipos.value = await listar()
  } catch (e) {
    toast.error('Error al cargar tipos de persona')
  } finally {
    loading.value = false
  }
}

const abrirModalCrear = () => {
  modal.abierto = true
  modal.editando = false
  Object.assign(form, { nombre: '', descripcion: '' })
  error.value = null
}

const abrirModalEditar = (t) => {
  modal.abierto = true
  modal.editando = true
  modal.id = t.id
  Object.assign(form, { nombre: t.nombre, descripcion: t.descripcion || '' })
  error.value = null
}

const cerrarModal = () => { modal.abierto = false }

const guardar = async () => {
  guardando.value = true
  error.value = null
  try {
    if (modal.editando) {
      await actualizar(modal.id, { descripcion: form.descripcion })
      toast.success('Tipo actualizado')
    } else {
      await crear({ ...form })
      toast.success('Tipo creado')
    }
    cerrarModal()
    await cargar()
  } catch (e) {
    error.value = e.response?.data?.detail || 'Error al guardar'
  } finally {
    guardando.value = false
  }
}

const confirmarEliminar = async (t) => {
  if (!confirm(`¿Eliminar "${t.nombre}"? Esta acción no se puede deshacer.`)) return
  try {
    await eliminar(t.id)
    toast.success('Tipo eliminado')
    await cargar()
  } catch (e) {
    toast.error('Error al eliminar')
  }
}

onMounted(cargar)
</script>