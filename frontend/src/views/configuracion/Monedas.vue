<template>
  <div class="max-w-7xl mx-auto">
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">💱 Monedas</h1>
        <p class="text-sm text-gray-500">Catálogo BANGUAT / ISO 4217</p>
      </div>
      <button v-if="authStore.isSuperAdmin" @click="abrirModalCrear" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2">
        <PlusIcon class="w-4 h-4" />
        Nueva Moneda
      </button>
    </div>

    <div class="bg-white rounded-lg shadow-sm border p-4 mb-4 flex gap-3">
      <input v-model="filtros.search" type="text" placeholder="Buscar por código o nombre..." class="flex-1 px-3 py-2 border rounded-lg text-sm" @input="debouncedCargar" />
      <select v-model="filtros.activo" @change="cargar" class="px-3 py-2 border rounded-lg text-sm">
        <option :value="null">Todos</option>
        <option :value="true">Activas</option>
        <option :value="false">Inactivas</option>
      </select>
    </div>

    <div class="bg-white rounded-lg shadow-sm border overflow-hidden">
      <div v-if="loading" class="p-8 text-center text-gray-500">Cargando...</div>
      <table v-else class="w-full">
        <thead class="bg-gray-50 border-b">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">BANGUAT</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">ISO</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Nombre</th>
            <th class="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase">Símbolo</th>
            <th class="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase">Decimales</th>
            <th class="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase">Estado</th>
            <th class="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y">
          <tr v-for="m in monedas" :key="m.id" class="hover:bg-gray-50">
            <td class="px-4 py-3 text-sm font-mono text-blue-600">{{ m.codigo_banguat }}</td>
            <td class="px-4 py-3 text-sm font-mono">{{ m.codigo_iso }}</td>
            <td class="px-4 py-3 text-sm font-medium">{{ m.nombre }}</td>
            <td class="px-4 py-3 text-sm text-center">{{ m.simbolo || '—' }}</td>
            <td class="px-4 py-3 text-sm text-center">{{ m.decimales }}</td>
            <td class="px-4 py-3 text-center">
              <span :class="m.activo ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-600'" class="px-2 py-1 rounded-full text-xs font-medium">
                {{ m.activo ? 'Activa' : 'Inactiva' }}
              </span>
            </td>
            <td v-if="authStore.isSuperAdmin" class="px-4 py-3 text-right space-x-2">
              <button @click="abrirModalEditar(m)" class="text-blue-600 hover:text-blue-800 text-sm">Editar</button>
              <button @click="toggleEstado(m)" :class="m.activo ? 'text-red-600' : 'text-emerald-600'" class="text-sm">
                {{ m.activo ? 'Desactivar' : 'Activar' }}
              </button>
            </td>
          </tr>
          <tr v-if="!monedas.length"><td colspan="7" class="px-4 py-8 text-center text-gray-500">No hay monedas registradas</td></tr>
        </tbody>
      </table>
    </div>

    <!-- Modal -->
    <div v-if="modal.abierto" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="cerrarModal">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
        <h2 class="text-xl font-bold mb-4">{{ modal.editando ? 'Editar Moneda' : 'Nueva Moneda' }}</h2>
        <form @submit.prevent="guardar" class="space-y-4">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Código BANGUAT *</label>
              <input v-model="form.codigo_banguat" type="text" required maxlength="5" :disabled="modal.editando" class="w-full px-3 py-2 border rounded-lg font-mono" placeholder="001" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Código ISO *</label>
              <input v-model="form.codigo_iso" type="text" required maxlength="3" :disabled="modal.editando" class="w-full px-3 py-2 border rounded-lg font-mono uppercase" placeholder="GTQ" />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nombre *</label>
            <input v-model="form.nombre" type="text" required maxlength="50" class="w-full px-3 py-2 border rounded-lg" placeholder="Quetzal" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Símbolo</label>
              <input v-model="form.simbolo" type="text" maxlength="5" class="w-full px-3 py-2 border rounded-lg" placeholder="Q" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Decimales</label>
              <input v-model.number="form.decimales" type="number" min="0" max="10" class="w-full px-3 py-2 border rounded-lg" />
            </div>
          </div>
          <div class="flex items-center gap-2">
            <input v-model="form.activo" type="checkbox" id="activo" class="rounded" />
            <label for="activo" class="text-sm">Activa</label>
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
import { useMonedasApi } from '@/composables/catalogos/useMonedasApi'
import { useToast } from '@/composables/useToast'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const { listar, crear, actualizar, eliminar } = useMonedasApi()
const toast = useToast()

const monedas = ref([])
const loading = ref(false)
const guardando = ref(false)
const error = ref(null)

const filtros = reactive({ search: '', activo: null })
const modal = reactive({ abierto: false, editando: false, id: null })
const form = reactive({ codigo_banguat: '', codigo_iso: '', nombre: '', simbolo: '', decimales: 2, activo: true })

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
    if (filtros.activo !== null) params.activo = filtros.activo
    const res = await listar(params)
    monedas.value = res.data
  } catch (e) {
    toast.error('Error al cargar monedas')
  } finally {
    loading.value = false
  }
}

const abrirModalCrear = () => {
  modal.abierto = true
  modal.editando = false
  modal.id = null
  Object.assign(form, { codigo_banguat: '', codigo_iso: '', nombre: '', simbolo: '', decimales: 2, activo: true })
  error.value = null
}

const abrirModalEditar = (m) => {
  modal.abierto = true
  modal.editando = true
  modal.id = m.id
  Object.assign(form, {
    codigo_banguat: m.codigo_banguat,
    codigo_iso: m.codigo_iso,
    nombre: m.nombre,
    simbolo: m.simbolo || '',
    decimales: m.decimales,
    activo: m.activo
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
      toast.success('Moneda actualizada')
    } else {
      await crear({ ...form })
      toast.success('Moneda creada')
    }
    cerrarModal()
    await cargar()
  } catch (e) {
    error.value = e.response?.data?.detail || 'Error al guardar'
  } finally {
    guardando.value = false
  }
}

const toggleEstado = async (m) => {
  try {
    await eliminar(m.id)
    toast.success(m.activo ? 'Moneda desactivada' : 'Moneda activada')
    await cargar()
  } catch (e) {
    toast.error('Error al actualizar estado')
  }
}

onMounted(cargar)
</script>