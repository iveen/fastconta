<!-- src/views/PlanCuentas.vue -->
<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-7xl mx-auto space-y-6">
      <div class="flex justify-between items-center">
        <h2 class="text-2xl font-bold text-gray-800">Plan de Cuentas</h2>
        <div class="space-x-2" v-if="empresaSeleccionadaId">
          <button @click="exportarExcel" class="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 flex items-center gap-2 text-sm font-medium">
            📤 Exportar Excel
          </button>
          <button @click="abrirModalImportar" class="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 flex items-center gap-2 text-sm font-medium">
            📥 Importar Excel
          </button>
          <button @click="abrirModalCrear" class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center gap-2 text-sm font-medium">
            ➕ Nueva Cuenta
          </button>
        </div>
      </div>

      <!-- Mensaje de error -->
      <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        {{ error }}
      </div>

      <!-- Mensaje de éxito -->
      <div v-if="successMessage" class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
        {{ successMessage }}
      </div>

      <!-- 🔹 SELECTOR DE TENANT (Solo Superadmin) -->
      <div v-if="authStore.isSuperAdmin" class="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <label class="block text-sm font-semibold text-blue-800 mb-1">🏢 Seleccionar Firma (Tenant)</label>
        <select
          v-model="selectedTenantId"
          @change="handleTenantChange"
          class="w-full md:w-1/2 border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 p-2 border bg-white"
        >
          <option value="">-- Seleccione una firma --</option>
          <option v-for="t in tenants" :key="t.id" :value="t.id">
            {{ t.name }} ({{ t.nit }})
          </option>
        </select>
      </div>

      <!-- Selector de empresa -->
      <div class="bg-white shadow-md rounded-lg p-4">
        <label class="block text-gray-700 text-sm font-bold mb-2">Seleccionar Empresa</label>
        <select
          v-model="empresaSeleccionadaId"
          @change="cargarCuentas"
          class="w-full md:w-1/3 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">-- Seleccione una empresa --</option>
          <option v-for="emp in empresas" :key="emp.id" :value="emp.id">
            {{ emp.nombre }}
          </option>
        </select>
      </div>

      <!-- Sin empresa seleccionada -->
      <div v-if="!empresaSeleccionadaId" class="bg-white shadow-md rounded-lg p-8 text-center text-gray-500">
        Seleccione una empresa para ver su plan de cuentas.
      </div>

      <!-- Listado de cuentas -->
      <div v-else>
        <div v-if="cargando" class="text-center py-8 text-gray-500">
          Cargando cuentas...
        </div>
        <div v-else-if="cuentas.length === 0" class="bg-white shadow-md rounded-lg p-8 text-center text-gray-500">
          No hay cuentas registradas para esta empresa.
        </div>
        <div v-else class="bg-white shadow-md rounded-lg overflow-hidden">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Código</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nombre</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Naturaleza</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nivel</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Acciones</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="cuenta in cuentas" :key="cuenta.id" class="hover:bg-gray-50">
                <td class="px-4 py-3 whitespace-nowrap text-sm font-mono text-gray-900" :style="{ paddingLeft: `${(cuenta.nivel - 1) * 1.5}rem` }">
                  {{ cuenta.codigo }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700" :style="{ paddingLeft: `${(cuenta.nivel - 1) * 1.5}rem` }">
                  {{ cuenta.nombre }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500 capitalize">
                  <span class="px-2 py-1 text-xs font-semibold rounded-full"
                    :class="{
                      'bg-blue-100 text-blue-800': cuenta.tipo === 'activo',
                      'bg-red-100 text-red-800': cuenta.tipo === 'pasivo',
                      'bg-purple-100 text-purple-800': cuenta.tipo === 'patrimonio',
                      'bg-green-100 text-green-800': cuenta.tipo === 'ingreso',
                      'bg-orange-100 text-orange-800': cuenta.tipo === 'gasto'
                    }">
                    {{ cuenta.tipo }}
                  </span>
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500 capitalize">{{ cuenta.naturaleza }}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500 text-center">{{ cuenta.nivel }}</td>
                <td class="px-4 py-3 whitespace-nowrap text-right text-sm font-medium">
                  <button @click="editarCuenta(cuenta)" class="text-indigo-600 hover:text-indigo-900 mr-3">Editar</button>
                  <button @click="confirmarEliminar(cuenta)" class="text-red-600 hover:text-red-900">Eliminar</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 🔹 MODAL: Crear/Editar Cuenta -->
    <div v-if="showFormModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-lg p-6 w-full max-w-2xl shadow-xl max-h-[90vh] overflow-y-auto">
        <h3 class="text-lg font-bold mb-4 text-gray-800">{{ isEditing ? 'Editar' : 'Nueva' }} Cuenta</h3>
        <form @submit.prevent="guardarCuenta" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700">Código *</label>
              <input v-model="form.codigo" :disabled="isEditing" required class="mt-1 block w-full border border-gray-300 rounded-md p-2 focus:ring-blue-500 focus:border-blue-500" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Nivel *</label>
              <input v-model.number="form.nivel" type="number" min="1" max="10" required class="mt-1 block w-full border border-gray-300 rounded-md p-2 focus:ring-blue-500 focus:border-blue-500" />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Nombre *</label>
            <input v-model="form.nombre" required class="mt-1 block w-full border border-gray-300 rounded-md p-2 focus:ring-blue-500 focus:border-blue-500" />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700">Tipo *</label>
              <select v-model="form.tipo" required class="mt-1 block w-full border border-gray-300 rounded-md p-2 focus:ring-blue-500 focus:border-blue-500">
                <option value="activo">Activo</option>
                <option value="pasivo">Pasivo</option>
                <option value="patrimonio">Patrimonio</option>
                <option value="ingreso">Ingreso</option>
                <option value="gasto">Gasto</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Naturaleza *</label>
              <select v-model="form.naturaleza" required class="mt-1 block w-full border border-gray-300 rounded-md p-2 focus:ring-blue-500 focus:border-blue-500">
                <option value="deudora">Deudora</option>
                <option value="acreedora">Acreedora</option>
              </select>
            </div>
          </div>

          <!-- 🔹 BUSCADOR DE CUENTA PADRE -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Cuenta Padre</label>
            <div class="relative">
              <input
                v-model="busquedaPadre"
                @focus="mostrarResultadosPadre = true"
                @input="filtrarCuentasPadre"
                type="text"
                placeholder="Buscar por código o nombre..."
                class="w-full border border-gray-300 rounded-md p-2 pr-10 focus:ring-blue-500 focus:border-blue-500"
              />
              <button
                v-if="form.cuenta_padre_id"
                @click="limpiarCuentaPadre"
                type="button"
                class="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <!-- Lista de resultados -->
            <div v-if="mostrarResultadosPadre && cuentasPadreFiltradas.length > 0" class="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-48 overflow-y-auto">
              <div
                v-for="cuenta in cuentasPadreFiltradas"
                :key="cuenta.id"
                @click="seleccionarCuentaPadre(cuenta)"
                class="px-3 py-2 hover:bg-blue-50 cursor-pointer border-b border-gray-100 last:border-b-0"
              >
                <div class="text-sm font-mono text-gray-900">{{ cuenta.codigo }}</div>
                <div class="text-xs text-gray-600">{{ cuenta.nombre }}</div>
              </div>
            </div>

            <!-- Cuenta seleccionada -->
            <div v-if="cuentaPadreSeleccionada" class="mt-2 p-2 bg-blue-50 border border-blue-200 rounded-md">
              <div class="text-sm">
                <span class="font-semibold">Seleccionada:</span>
                <span class="font-mono">{{ cuentaPadreSeleccionada.codigo }}</span> - {{ cuentaPadreSeleccionada.nombre }}
              </div>
            </div>
          </div>

          <div class="flex items-center gap-2 pt-2">
            <input v-model="form.acepta_tercero" type="checkbox" id="tercero" class="rounded border-gray-300 text-blue-600 focus:ring-blue-500 h-4 w-4" />
            <label for="tercero" class="text-sm text-gray-700">Acepta Terceros (Clientes/Proveedores/Empleados)</label>
          </div>
          <div class="flex justify-end gap-2 pt-4 border-t border-gray-100">
            <button type="button" @click="showFormModal = false" class="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-md">Cancelar</button>
            <button type="submit" :disabled="cargando" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50">
              {{ cargando ? 'Guardando...' : 'Guardar' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 🔹 MODAL: Confirmar Eliminación -->
    <div v-if="showDeleteModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-lg p-6 w-full max-w-md shadow-xl">
        <h3 class="text-lg font-bold mb-4 text-gray-800">Confirmar Eliminación</h3>
        <p class="text-sm text-gray-600 mb-4">
          ¿Está seguro de eliminar la cuenta <strong>{{ cuentaAEliminar?.codigo }}</strong> - {{ cuentaAEliminar?.nombre }}?
        </p>
        <p class="text-xs text-gray-500 mb-4">
          La cuenta se marcará como inactiva y no se mostrará en los listados, pero se preservará para mantener la integridad de las partidas existentes.
        </p>
        <div class="flex justify-end gap-2">
          <button @click="showDeleteModal = false" class="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-md">Cancelar</button>
          <button @click="eliminarCuenta" :disabled="cargando" class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50">
            {{ cargando ? 'Eliminando...' : 'Eliminar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 🔹 MODAL: Importar Excel -->
    <div v-if="showImportModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-lg p-6 w-full max-w-md shadow-xl">
        <h3 class="text-lg font-bold mb-2 text-gray-800">Importar Plan de Cuentas</h3>
        <p class="text-sm text-gray-600 mb-4">El archivo Excel debe contener las columnas: <b>codigo, nombre, tipo, naturaleza, nivel</b> y opcionalmente <b>cuenta_padre_codigo</b>.</p>
        <input type="file" @change="handleFileUpload" accept=".xlsx, .xls" class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 mb-4 border border-gray-300 rounded-md p-2"/>
        <div class="flex justify-end gap-2">
          <button @click="showImportModal = false" class="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-md">Cancelar</button>
          <button @click="subirExcel" :disabled="!selectedFile || cargando" class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 flex items-center gap-2">
            <span v-if="cargando">⏳ Procesando...</span>
            <span v-else>📥 Importar</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

const authStore = useAuthStore()
const tenants = ref([])
const selectedTenantId = ref('')
const empresas = ref([])
const empresaSeleccionadaId = ref('')
const cuentas = ref([])
const cargando = ref(false)
const error = ref('')
const successMessage = ref('')

// Modales
const showFormModal = ref(false)
const showDeleteModal = ref(false)
const showImportModal = ref(false)
const isEditing = ref(false)

// Formulario
const form = ref({
  codigo: '',
  nombre: '',
  tipo: 'activo',
  naturaleza: 'deudora',
  nivel: 1,
  cuenta_padre_id: null,
  acepta_tercero: false
})

// Eliminación
const cuentaAEliminar = ref(null)

// Importación
const selectedFile = ref(null)

// Buscador de cuenta padre
const busquedaPadre = ref('')
const mostrarResultadosPadre = ref(false)
const cuentaPadreSeleccionada = ref(null)

// Computed: Filtrar cuentas para el buscador de padre
const cuentasPadreFiltradas = computed(() => {
  if (!busquedaPadre.value) return cuentas.value
  const termino = busquedaPadre.value.toLowerCase()
  return cuentas.value.filter(c =>
    c.codigo.toLowerCase().includes(termino) ||
    c.nombre.toLowerCase().includes(termino)
  )
})

// 🔹 Cargar lista de tenants solo si es superadmin
const fetchTenants = async () => {
  if (!authStore.isSuperAdmin) return
  try {
    const res = await api.get('/tenants/')
    tenants.value = res.data.filter(t => !['sistema', 'system', 'public'].includes(t.schema_name))
  } catch (err) {
    console.error('Error cargando tenants:', err)
  }
}

const cargarEmpresas = async () => {
  if (authStore.isSuperAdmin && !selectedTenantId.value) {
    empresas.value = []
    return
  }
  try {
    const params = authStore.isSuperAdmin ? { tenant_id: selectedTenantId.value } : {}
    const response = await api.get('/empresas/', { params })
    empresas.value = response.data
  } catch (err) {
    error.value = 'Error al cargar empresas'
  }
}

const handleTenantChange = () => {
  empresaSeleccionadaId.value = ''
  cuentas.value = []
  cargarEmpresas()
}

const cargarCuentas = async () => {
  if (!empresaSeleccionadaId.value) {
    cuentas.value = []
    return
  }
  cargando.value = true
  error.value = ''
  successMessage.value = ''
  try {
    const params = { empresa_id: empresaSeleccionadaId.value }
    if (authStore.isSuperAdmin && selectedTenantId.value) {
      params.tenant_id = selectedTenantId.value
    }
    const response = await api.get('/plan-cuentas/', { params })
    cuentas.value = response.data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al cargar cuentas'
  } finally {
    cargando.value = false
  }
}

// 🔹 CRUD: Crear
const abrirModalCrear = () => {
  isEditing.value = false
  form.value = {
    codigo: '',
    nombre: '',
    tipo: 'activo',
    naturaleza: 'deudora',
    nivel: 1,
    cuenta_padre_id: null,
    acepta_tercero: false
  }
  busquedaPadre.value = ''
  cuentaPadreSeleccionada.value = null
  showFormModal.value = true
}

// 🔹 CRUD: Editar
const editarCuenta = (cuenta) => {
  isEditing.value = true
  form.value = {
    id: cuenta.id,
    codigo: cuenta.codigo,
    nombre: cuenta.nombre,
    tipo: cuenta.tipo,
    naturaleza: cuenta.naturaleza,
    nivel: cuenta.nivel,
    cuenta_padre_id: cuenta.cuenta_padre_id,
    acepta_tercero: cuenta.acepta_tercero
  }
  
  // Si tiene cuenta padre, mostrarla en el buscador
  if (cuenta.cuenta_padre_id) {
    const padre = cuentas.value.find(c => c.id === cuenta.cuenta_padre_id)
    if (padre) {
      cuentaPadreSeleccionada.value = padre
      busquedaPadre.value = `${padre.codigo} - ${padre.nombre}`
    }
  } else {
    cuentaPadreSeleccionada.value = null
    busquedaPadre.value = ''
  }
  
  showFormModal.value = true
}

// 🔹 CRUD: Guardar (Crear/Editar)
const guardarCuenta = async () => {
  cargando.value = true
  error.value = ''
  successMessage.value = ''
  
  try {
    const payload = {
      ...form.value,
      empresa_id: empresaSeleccionadaId.value
    }
    
    if (isEditing.value) {
      await api.put(`/plan-cuentas/${form.value.id}`, payload)
      successMessage.value = 'Cuenta actualizada correctamente'
    } else {
      await api.post('/plan-cuentas/', payload)
      successMessage.value = 'Cuenta creada correctamente'
    }
    
    showFormModal.value = false
    await cargarCuentas()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al guardar la cuenta'
  } finally {
    cargando.value = false
  }
}

// 🔹 CRUD: Eliminar (Soft Delete)
const confirmarEliminar = (cuenta) => {
  cuentaAEliminar.value = cuenta
  showDeleteModal.value = true
}

const eliminarCuenta = async () => {
  if (!cuentaAEliminar.value) return
  
  cargando.value = true
  error.value = ''
  successMessage.value = ''
  
  try {
    await api.delete(`/plan-cuentas/${cuentaAEliminar.value.id}`)
    successMessage.value = 'Cuenta eliminada correctamente'
    showDeleteModal.value = false
    cuentaAEliminar.value = null
    await cargarCuentas()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al eliminar la cuenta'
  } finally {
    cargando.value = false
  }
}

// 🔹 Buscador de Cuenta Padre
const filtrarCuentasPadre = () => {
  mostrarResultadosPadre.value = true
}

const seleccionarCuentaPadre = (cuenta) => {
  form.value.cuenta_padre_id = cuenta.id
  cuentaPadreSeleccionada.value = cuenta
  busquedaPadre.value = `${cuenta.codigo} - ${cuenta.nombre}`
  mostrarResultadosPadre.value = false
}

const limpiarCuentaPadre = () => {
  form.value.cuenta_padre_id = null
  cuentaPadreSeleccionada.value = null
  busquedaPadre.value = ''
}

// 🔹 Importación Excel
const abrirModalImportar = () => {
  selectedFile.value = null
  showImportModal.value = true
}

const handleFileUpload = (event) => {
  selectedFile.value = event.target.files[0]
}

const subirExcel = async () => {
  if (!selectedFile.value || !empresaSeleccionadaId.value) return
  
  cargando.value = true
  error.value = ''
  successMessage.value = ''
  
  const formData = new FormData()
  formData.append('file', selectedFile.value)
  formData.append('empresa_id', empresaSeleccionadaId.value)
  
  try {
    const response = await api.post('/plan-cuentas/importar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    successMessage.value = response.data.mensaje
    showImportModal.value = false
    await cargarCuentas()
  } catch (err) {
    if (err.response?.data?.detail?.errores) {
      error.value = "Errores en el archivo:\n• " + err.response.data.detail.errores.join('\n• ')
    } else {
      error.value = err.response?.data?.detail || 'Error al importar el archivo'
    }
  } finally {
    cargando.value = false
  }
}

// 🔹 Lógica de Exportación
const exportarExcel = async () => {
  if (!empresaSeleccionadaId.value) return
  
  try {
    cargando.value = true
    error.value = ''
    
    // Solicitar el archivo como blob
    const response = await api.get('/plan-cuentas/exportar', {
      params: { empresa_id: empresaSeleccionadaId.value },
      responseType: 'blob' // 🔹 CRÍTICO: Indica que esperamos un archivo binario
    })
    
    // Crear URL temporal y forzar descarga
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `plan_cuentas_${empresaSeleccionadaId.value}.xlsx`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    
    // Liberar memoria
    window.URL.revokeObjectURL(url)
    
    successMessage.value = '✅ Archivo exportado correctamente.'
  } catch (err) {
    if (err.response?.status === 404) {
      error.value = 'No hay cuentas activas para exportar.'
    } else {
      error.value = err.response?.data?.detail || 'Error al generar el archivo.'
    }
  } finally {
    cargando.value = false
  }
}

onMounted(async () => {
  await fetchTenants()
  if (authStore.isSuperAdmin && tenants.value.length > 0) {
    selectedTenantId.value = tenants.value[0].id
  }
  await cargarEmpresas()
})
</script>