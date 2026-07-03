<!-- src/views/configuracion/TiposDTE.vue -->
<template>
  <div class="max-w-7xl mx-auto">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">Tipos DTE</h1>
        <p class="text-sm text-gray-500">Catálogo de documentos tributarios electrónicos</p>
      </div>
      <div class="flex gap-2">
        <button
          @click="abrirModalImportar"
          class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 flex items-center gap-2"
        >
          <UploadIcon class="w-4 h-4" />
          Importar
        </button>
        <button
          @click="exportarExcel"
          class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 flex items-center gap-2"
        >
          <DownloadIcon class="w-4 h-4" />
          Exportar
        </button>
        <button
          @click="abrirModalCrear"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <PlusIcon class="w-4 h-4" />
          Nuevo Tipo DTE
        </button>
      </div>
    </div>

    <!-- Filtros -->
    <div class="bg-white rounded-lg shadow-sm border p-4 mb-4 flex gap-3">
      <select v-model="filtros.activo" @change="cargar" class="px-3 py-2 border rounded-lg text-sm">
        <option :value="null">Todos</option>
        <option :value="true">Activos</option>
        <option :value="false">Inactivos</option>
      </select>
      <select v-model="filtros.es_factura" @change="cargar" class="px-3 py-2 border rounded-lg text-sm">
        <option :value="null">Todos los tipos</option>
        <option :value="true">Facturas</option>
        <option :value="false">Otros documentos</option>
      </select>
    </div>

    <!-- Tabla -->
    <div class="bg-white rounded-lg shadow-sm border overflow-hidden">
      <div v-if="loading" class="p-8 text-center text-gray-500">Cargando...</div>
      <table v-else class="w-full">
        <thead class="bg-gray-50 border-b">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Código</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Descripción</th>
            <th class="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase">Complemento</th>
            <th class="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase">Es Factura</th>
            <th class="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase">Estado</th>
            <th class="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y">
          <tr v-for="dte in dtes" :key="dte.id" class="hover:bg-gray-50">
            <td class="px-4 py-3 text-sm font-mono text-blue-600">{{ dte.codigo }}</td>
            <td class="px-4 py-3 text-sm">{{ dte.descripcion }}</td>
            <td class="px-4 py-3 text-center">
              <span :class="dte.requiere_complemento ? 'text-amber-600' : 'text-gray-400'">
                {{ dte.requiere_complemento ? 'Sí' : 'No' }}
              </span>
            </td>
            <td class="px-4 py-3 text-center">
              <span :class="dte.es_factura ? 'text-emerald-600' : 'text-gray-500'">
                {{ dte.es_factura ? '✓' : '—' }}
              </span>
            </td>
            <td class="px-4 py-3 text-center">
              <span
                :class="dte.activo ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-600'"
                class="px-2 py-1 rounded-full text-xs font-medium"
              >
                {{ dte.activo ? 'Activo' : 'Inactivo' }}
              </span>
            </td>
            <td class="px-4 py-3 text-right space-x-2">
              <button @click="abrirModalEditar(dte)" class="text-blue-600 hover:text-blue-800 text-sm">Editar</button>
              <button
                @click="confirmarEliminar(dte)"
                :class="dte.activo ? 'text-red-600' : 'text-emerald-600'"
                class="text-sm"
              >
                {{ dte.activo ? 'Desactivar' : 'Activar' }}
              </button>
            </td>
          </tr>
          <tr v-if="!dtes.length">
            <td colspan="6" class="px-4 py-8 text-center text-gray-500">No hay tipos DTE registrados</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal Crear/Editar -->
    <div v-if="modal.abierto" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="cerrarModal">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
        <h2 class="text-xl font-bold mb-4">{{ modal.editando ? 'Editar Tipo DTE' : 'Nuevo Tipo DTE' }}</h2>
        <form @submit.prevent="guardar" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Código *</label>
            <input
              v-model="form.codigo"
              type="text"
              required
              :disabled="modal.editando"
              maxlength="10"
              class="w-full px-3 py-2 border rounded-lg font-mono"
              placeholder="Ej: FCAM"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Descripción *</label>
            <input v-model="form.descripcion" type="text" required maxlength="100" class="w-full px-3 py-2 border rounded-lg" />
          </div>
          <div class="flex gap-6">
            <label class="flex items-center gap-2">
              <input v-model="form.requiere_complemento" type="checkbox" class="rounded" />
              <span class="text-sm">Requiere complemento</span>
            </label>
            <label class="flex items-center gap-2">
              <input v-model="form.es_factura" type="checkbox" class="rounded" />
              <span class="text-sm">Es factura</span>
            </label>
            <label class="flex items-center gap-2">
              <input v-model="form.activo" type="checkbox" class="rounded" />
              <span class="text-sm">Activo</span>
            </label>
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

    <!-- Modal Importar -->
    <div v-if="modalImportar.abierto" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="modalImportar.abierto = false">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <h2 class="text-xl font-bold mb-4">Importar Tipos DTE</h2>
        <input type="file" ref="fileInput" accept=".xlsx,.xls" @change="onFileSelected" class="w-full text-sm mb-4" />
        <label class="flex items-center gap-2 mb-4">
          <input v-model="modalImportar.sobrescribir" type="checkbox" class="rounded" />
          <span class="text-sm">Sobrescribir registros existentes</span>
        </label>
        <div v-if="importResult" class="bg-gray-50 p-3 rounded-lg text-sm mb-4 space-y-1">
          <p>✅ Creados: <strong>{{ importResult.creados }}</strong></p>
          <p>🔄 Actualizados: <strong>{{ importResult.actualizados }}</strong></p>
          <p>⏭️ Omitidos: <strong>{{ importResult.omitidos }}</strong></p>
          <p v-if="importResult.errores.length" class="text-red-600">
            ❌ Errores: {{ importResult.errores.length }}
          </p>
        </div>
        <div class="flex justify-end gap-2">
          <button @click="modalImportar.abierto = false" class="px-4 py-2 border rounded-lg">Cerrar</button>
          <button
            @click="ejecutarImportar"
            :disabled="!archivoSeleccionado || importando"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50"
          >
            {{ importando ? 'Importando...' : 'Importar' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Plus as PlusIcon, Upload as UploadIcon, Download as DownloadIcon } from '@lucide/vue'
import { useTiposDTEApi } from '@/composables/configuracion/useTiposDTEApi'
import { useToast } from '@/composables/useToast'

const { listar, crear, actualizar, eliminar, exportarExcel, importarExcel } = useTiposDTEApi()
const toast = useToast()

const dtes = ref([])
const loading = ref(false)
const guardando = ref(false)
const importando = ref(false)
const error = ref(null)
const archivoSeleccionado = ref(null)
const importResult = ref(null)

const filtros = reactive({ activo: null, es_factura: null })
const modal = reactive({ abierto: false, editando: false, id: null })
const modalImportar = reactive({ abierto: false, sobrescribir: false })

const form = reactive({
  codigo: '',
  descripcion: '',
  requiere_complemento: false,
  es_factura: true,
  activo: true
})

const cargar = async () => {
  loading.value = true
  try {
    const params = { skip: 0, limit: 200 }
    if (filtros.activo !== null) params.activo = filtros.activo
    if (filtros.es_factura !== null) params.es_factura = filtros.es_factura
    const res = await listar(params)
    dtes.value = res.data
  } catch (e) {
    toast.error('Error al cargar tipos DTE')
  } finally {
    loading.value = false
  }
}

const abrirModalCrear = () => {
  modal.abierto = true
  modal.editando = false
  Object.assign(form, { codigo: '', descripcion: '', requiere_complemento: false, es_factura: true, activo: true })
  error.value = null
}

const abrirModalEditar = (dte) => {
  modal.abierto = true
  modal.editando = true
  modal.id = dte.id
  Object.assign(form, {
    codigo: dte.codigo,
    descripcion: dte.descripcion,
    requiere_complemento: dte.requiere_complemento,
    es_factura: dte.es_factura,
    activo: dte.activo
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
      toast.success('Tipo DTE actualizado')
    } else {
      await crear({ ...form })
      toast.success('Tipo DTE creado')
    }
    cerrarModal()
    await cargar()
  } catch (e) {
    error.value = e.response?.data?.detail || 'Error al guardar'
  } finally {
    guardando.value = false
  }
}

const confirmarEliminar = async (dte) => {
  if (!confirm(`¿${dte.activo ? 'Desactivar' : 'Activar'} "${dte.codigo}"?`)) return
  try {
    await eliminar(dte.id)
    toast.success('Estado actualizado')
    await cargar()
  } catch (e) {
    toast.error('Error al actualizar')
  }
}

const onFileSelected = (e) => {
  archivoSeleccionado.value = e.target.files[0] || null
  importResult.value = null
}

const abrirModalImportar = () => {
  modalImportar.abierto = true
  archivoSeleccionado.value = null
  importResult.value = null
}

const ejecutarImportar = async () => {
  if (!archivoSeleccionado.value) return
  importando.value = true
  try {
    importResult.value = await importarExcel(archivoSeleccionado.value, modalImportar.sobrescribir)
    toast.success('Importación completada')
    await cargar()
  } catch (e) {
    toast.error('Error al importar')
  } finally {
    importando.value = false
  }
}

const handleExportar = async () => {
  try {
    await exportarExcel()
    toast.success('Archivo descargado')
  } catch (e) {
    toast.error('Error al exportar')
  }
}

// Exponer con alias para el template
const exportar = handleExportar

onMounted(cargar)
</script>