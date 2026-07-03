<template>
  <div class="max-w-7xl mx-auto">
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">🗺️ Geografía</h1>
        <p class="text-sm text-gray-500">Departamentos y municipios de Guatemala</p>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Panel izquierdo: Departamentos -->
      <div class="bg-white rounded-lg shadow-sm border">
        <div class="p-4 border-b flex justify-between items-center">
          <h2 class="font-semibold text-gray-800">Departamentos ({{ departamentos.length }})</h2>
          <button v-if="authStore.isSuperAdmin" @click="abrirModalDepto" class="px-2 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700">+ Nuevo</button>
        </div>
        <ul class="divide-y max-h-[600px] overflow-y-auto">
          <li
            v-for="d in departamentos"
            :key="d.id"
            @click="seleccionarDepartamento(d)"
            class="p-3 cursor-pointer hover:bg-blue-50 flex items-center justify-between"
            :class="{ 'bg-blue-50 border-l-4 border-blue-600': deptoSeleccionado?.id === d.id }"
          >
            <div>
              <p class="font-mono text-xs text-gray-500">{{ d.codigo_iso }}</p>
              <p class="text-sm font-medium">{{ d.nombre }}</p>
              <p class="text-xs text-gray-500">{{ d.municipios?.length || 0 }} municipios</p>
            </div>
            <div class="flex gap-1">
              <div v-if="authStore.isSuperAdmin" class="flex gap-1">
                <button @click.stop="editarDepartamento(d)" class="text-blue-600 text-xs hover:underline">✏️</button>
                <button @click.stop="handleEliminarDepartamento(d)" class="text-red-600 text-xs hover:underline">🗑️</button>
              </div>
            </div>
          </li>
        </ul>
      </div>

      <!-- Panel derecho: Municipios -->
      <div class="lg:col-span-2 bg-white rounded-lg shadow-sm border">
        <div class="p-4 border-b flex justify-between items-center">
          <div>
            <h2 class="font-semibold text-gray-800">Municipios de {{ deptoSeleccionado?.nombre || '...' }}</h2>
            <p class="text-xs text-gray-500">{{ municipios.length }} registrados</p>
          </div>
          <button v-if="deptoSeleccionado && authStore.isSuperAdmin" @click="abrirModalMuni" class="px-2 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700">+ Nuevo</button>
        </div>
        <div v-if="!deptoSeleccionado" class="p-12 text-center text-gray-500">Selecciona un departamento para ver sus municipios</div>
        <div v-else-if="loadingMunis" class="p-8 text-center text-gray-500">Cargando...</div>
        <table v-else class="w-full">
          <thead class="bg-gray-50 border-b">
            <tr>
              <th class="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">Código</th>
              <th class="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">Nombre</th>
              <th class="px-4 py-2 text-right text-xs font-semibold text-gray-600 uppercase">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y">
            <tr v-for="m in municipios" :key="m.id" class="hover:bg-gray-50">
              <td class="px-4 py-2 text-sm font-mono text-blue-600">{{ m.codigo_iso }}</td>
              <td class="px-4 py-2 text-sm">{{ m.nombre }}</td>
              <td class="px-4 py-2 text-right space-x-2">
                <template v-if="authStore.isSuperAdmin">
                    <button @click="editarMunicipio(m)" class="text-blue-600 text-sm">Editar</button>
                    <button @click="handleEliminarMunicipio(m)" class="text-red-600 text-sm">Eliminar</button>
                    <button @click="editarMunicipio(m)" class="text-blue-600 text-sm">Editar</button>
                    <button @click="handleEliminarMunicipio(m)" class="text-red-600 text-sm">Eliminar</button>
                </template>
                <span v-else class="text-xs text-gray-400">Solo lectura</span>
              </td>
            </tr>
            <tr v-if="!municipios.length">
              <td colspan="3" class="px-4 py-8 text-center text-gray-500">No hay municipios registrados</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal Departamento -->
    <div v-if="modalDepto.abierto" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="modalDepto.abierto = false">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <h2 class="text-xl font-bold mb-4">{{ modalDepto.editando ? 'Editar Departamento' : 'Nuevo Departamento' }}</h2>
        <form @submit.prevent="guardarDepto" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Código ISO *</label>
            <input v-model="formDepto.codigo_iso" type="text" required maxlength="2" :disabled="modalDepto.editando" class="w-full px-3 py-2 border rounded-lg font-mono" placeholder="01" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nombre *</label>
            <input v-model="formDepto.nombre" type="text" required maxlength="100" class="w-full px-3 py-2 border rounded-lg" placeholder="Guatemala" />
          </div>
          <div v-if="errorDepto" class="text-sm text-red-600 bg-red-50 p-2 rounded">{{ errorDepto }}</div>
          <div class="flex justify-end gap-2 pt-2">
            <button type="button" @click="modalDepto.abierto = false" class="px-4 py-2 border rounded-lg">Cancelar</button>
            <button type="submit" :disabled="guardandoDepto" class="px-4 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50">
              {{ guardandoDepto ? 'Guardando...' : 'Guardar' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal Municipio -->
    <div v-if="modalMuni.abierto" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="modalMuni.abierto = false">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <h2 class="text-xl font-bold mb-4">{{ modalMuni.editando ? 'Editar Municipio' : 'Nuevo Municipio' }}</h2>
        <form @submit.prevent="guardarMuni" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Código ISO *</label>
            <input v-model="formMuni.codigo_iso" type="text" required maxlength="4" :disabled="modalMuni.editando" class="w-full px-3 py-2 border rounded-lg font-mono" placeholder="0101" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nombre *</label>
            <input v-model="formMuni.nombre" type="text" required maxlength="100" class="w-full px-3 py-2 border rounded-lg" placeholder="Guatemala" />
          </div>
          <div v-if="errorMuni" class="text-sm text-red-600 bg-red-50 p-2 rounded">{{ errorMuni }}</div>
          <div class="flex justify-end gap-2 pt-2">
            <button type="button" @click="modalMuni.abierto = false" class="px-4 py-2 border rounded-lg">Cancelar</button>
            <button type="submit" :disabled="guardandoMuni" class="px-4 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50">
              {{ guardandoMuni ? 'Guardando...' : 'Guardar' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useGeografiaApi } from '@/composables/catalogos/useGeografiaApi'
import { useToast } from '@/composables/useToast'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const {
  listarDepartamentos, crearDepartamento, actualizarDepartamento, eliminarDepartamento,
  listarMunicipios, crearMunicipio, actualizarMunicipio, eliminarMunicipio
} = useGeografiaApi()

const toast = useToast()

const departamentos = ref([])
const municipios = ref([])
const deptoSeleccionado = ref(null)
const loadingMunis = ref(false)

const modalDepto = reactive({ abierto: false, editando: false, id: null })
const formDepto = reactive({ codigo_iso: '', nombre: '' })
const guardandoDepto = ref(false)
const errorDepto = ref(null)

const modalMuni = reactive({ abierto: false, editando: false, id: null })
const formMuni = reactive({ codigo_iso: '', nombre: '' })
const guardandoMuni = ref(false)
const errorMuni = ref(null)

const cargarDepartamentos = async () => {
  try {
    departamentos.value = await listarDepartamentos()
    console.log('Departamentos cargados:', departamentos.value)
  } catch (e) {
    toast.error('Error al cargar departamentos')
  }
}

const seleccionarDepartamento = async (d) => {
  deptoSeleccionado.value = d
  loadingMunis.value = true
  try {
    municipios.value = await listarMunicipios(d.id)
  } catch (e) {
    toast.error('Error al cargar municipios')
  } finally {
    loadingMunis.value = false
  }
}

const abrirModalDepto = () => {
  modalDepto.abierto = true
  modalDepto.editando = false
  Object.assign(formDepto, { codigo_iso: '', nombre: '' })
  errorDepto.value = null
}

const editarDepartamento = (d) => {
  modalDepto.abierto = true
  modalDepto.editando = true
  modalDepto.id = d.id
  Object.assign(formDepto, { codigo_iso: d.codigo_iso, nombre: d.nombre })
  errorDepto.value = null
}

const guardarDepto = async () => {
  guardandoDepto.value = true
  errorDepto.value = null
  try {
    if (modalDepto.editando) {
      await actualizarDepartamento(modalDepto.id, { nombre: formDepto.nombre })
      toast.success('Departamento actualizado')
    } else {
      await crearDepartamento({ ...formDepto })
      toast.success('Departamento creado')
    }
    modalDepto.abierto = false
    await cargarDepartamentos()
  } catch (e) {
    errorDepto.value = e.response?.data?.detail || 'Error al guardar'
  } finally {
    guardandoDepto.value = false
  }
}

const handleEliminarDepartamento = async (d) => {
  if (!confirm(`¿Eliminar "${d.nombre}" y todos sus municipios?`)) return
  try {
    await eliminarDepartamento(d.id)
    toast.success('Departamento eliminado')
    if (deptoSeleccionado.value?.id === d.id) {
      deptoSeleccionado.value = null
      municipios.value = []
    }
    await cargarDepartamentos()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Error al eliminar')
  }
}

const abrirModalMuni = () => {
  modalMuni.abierto = true
  modalMuni.editando = false
  Object.assign(formMuni, { codigo_iso: '', nombre: '' })
  errorMuni.value = null
}

const editarMunicipio = (m) => {
  modalMuni.abierto = true
  modalMuni.editando = true
  modalMuni.id = m.id
  Object.assign(formMuni, { codigo_iso: m.codigo_iso, nombre: m.nombre })
  errorMuni.value = null
}

const guardarMuni = async () => {
  guardandoMuni.value = true
  errorMuni.value = null
  try {
    const payload = {
      ...formMuni,
      departamento_id: deptoSeleccionado.value.id
    }
    if (modalMuni.editando) {
      await actualizarMunicipio(modalMuni.id, { nombre: formMuni.nombre })
      toast.success('Municipio actualizado')
    } else {
      await crearMunicipio(payload)
      toast.success('Municipio creado')
    }
    modalMuni.abierto = false
    await seleccionarDepartamento(deptoSeleccionado.value)
  } catch (e) {
    errorMuni.value = e.response?.data?.detail || 'Error al guardar'
  } finally {
    guardandoMuni.value = false
  }
}

const handleEliminarMunicipio = async (m) => {
  if (!confirm(`¿Eliminar "${m.nombre}"?`)) return
  try {
    await eliminarMunicipio(m.id)
    toast.success('Municipio eliminado')
    await seleccionarDepartamento(deptoSeleccionado.value)
    await cargarDepartamentos()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Error al eliminar')
  }
}

onMounted(cargarDepartamentos)
</script>