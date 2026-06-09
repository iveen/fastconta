<!-- src/views/Empresas.vue -->
<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-6xl mx-auto space-y-6">
      <div class="flex justify-between items-center">
        <h1 class="text-2xl font-bold text-gray-800">Empresas</h1>
      </div>

      <!-- 🔹 SELECTOR DE TENANT (Solo Superadmin) -->
      <div v-if="authStore.isSuperAdmin" class="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <label class="block text-sm font-semibold text-blue-800 mb-1">🏢 Seleccionar Firma (Tenant)</label>
        <select
          v-model="selectedTenantId"
          @change="handleTenantChange"
          class="w-full md:w-1/2 border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 p-2 border bg-white"
        >
          <option value="">-- Seleccione una firma para gestionar --</option>
          <option v-for="t in tenants" :key="t.id" :value="t.id">
            {{ t.name }} ({{ t.nit }})
          </option>
        </select>
      </div>

      <!-- Mensajes -->
      <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">{{ error }}</div>
      <div v-if="successMsg" class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded flex justify-between items-center">
        <span>{{ successMsg }}</span>
        <button @click="successMsg = ''" class="text-sm underline hover:no-underline">Cerrar</button>
      </div>

      <!-- Estado vacío para superadmin sin tenant seleccionado -->
      <div v-if="authStore.isSuperAdmin && !selectedTenantId" class="bg-white rounded-lg shadow p-12 text-center border border-gray-200">
        <svg class="mx-auto h-16 w-16 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
        <p class="mt-4 text-gray-500 text-lg">Seleccione una firma en el filtro superior para visualizar sus empresas.</p>
      </div>

      <!-- Contenido principal -->
      <div v-else class="space-y-6">
        <!-- Botón Nueva Empresa -->
        <div v-if="!authStore.isSuperAdmin" class="flex justify-end">
          <button @click="mostrarFormulario = !mostrarFormulario" class="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600 transition">
            {{ mostrarFormulario ? 'Cancelar' : 'Nueva Empresa' }}
          </button>
        </div>

        <!-- Formulario de creación -->
        <div v-if="mostrarFormulario && !authStore.isSuperAdmin" class="bg-white shadow-md rounded-lg p-6">
          <h3 class="text-lg font-semibold mb-4">Nueva Empresa</h3>
          <form @submit.prevent="crearEmpresa">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-gray-700 text-sm font-bold mb-2">Nombre</label>
                <input v-model="nuevaEmpresa.nombre" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" required />
              </div>
              <div>
                <label class="block text-gray-700 text-sm font-bold mb-2">NIT</label>
                <input v-model="nuevaEmpresa.nit" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" required />
              </div>
              <div class="md:col-span-2">
                <label class="block text-gray-700 text-sm font-bold mb-2">Dirección</label>
                <input v-model="nuevaEmpresa.direccion" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
            </div>
            <button type="submit" :disabled="cargando" class="mt-4 bg-green-500 text-white px-6 py-2 rounded-md hover:bg-green-600 transition disabled:opacity-50">
              {{ cargando ? 'Creando...' : 'Crear Empresa' }}
            </button>
          </form>
        </div>

        <!-- Listado de empresas -->
        <div v-if="cargandoLista" class="text-center py-8 text-gray-500">Cargando empresas...</div>
        <div v-else-if="empresas.length === 0" class="bg-white shadow-md rounded-lg p-8 text-center text-gray-500">No hay empresas registradas.</div>
        <div v-else class="bg-white shadow-md rounded-lg overflow-hidden">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nombre</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">NIT</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Dirección</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estado Cierre</th>
                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Acciones</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="empresa in empresas" :key="empresa.id">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ empresa.nombre }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ empresa.nit }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ empresa.direccion || '-' }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                  <span v-if="empresa.cuenta_utilidad_periodo_id && empresa.cuenta_utilidades_acumuladas_id" class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                    ✅ Configurada
                  </span>
                  <span v-else class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">
                    ⚠️ Pendiente
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-right">
                  <button @click="abrirConfiguracion(empresa)" class="text-blue-600 hover:text-blue-900 font-medium">
                    ⚙️ Configurar
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 🔹 MODAL DE CONFIGURACIÓN CON BÚSQUEDA -->
      <div v-if="showConfigModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center z-50">
        <div class="bg-white p-6 rounded-lg shadow-xl max-w-lg w-full mx-4 relative">
          <!-- Botón cerrar modal -->
          <button @click="cerrarConfigModal" class="absolute top-4 right-4 text-gray-400 hover:text-gray-600">✕</button>

          <h3 class="text-lg font-bold mb-4 text-gray-800 pr-6">Configurar Cuentas de Cierre</h3>
          <p class="text-sm text-gray-500 mb-4">Empresa: <span class="font-medium">{{ empresaConfig?.nombre }}</span></p>
          
          <div v-if="errorConfig" class="bg-red-100 border border-red-400 text-red-700 px-3 py-2 rounded mb-4 text-sm">{{ errorConfig }}</div>
          <div v-if="successConfig" class="bg-green-100 border border-green-400 text-green-700 px-3 py-2 rounded mb-4 text-sm">{{ successConfig }}</div>

          <div class="space-y-5">
            
            <!-- 🔍 BÚSQUEDA: Utilidad del Período -->
            <div class="relative">
              <label class="block text-gray-700 text-sm font-bold mb-1">Cuenta Utilidad/Pérdida del Período</label>
              <div class="relative rounded-md shadow-sm">
                <input 
                  type="text" 
                  v-model="busquedaUtilidad" 
                  @focus="dropdownUtilidad = true"
                  @blur="handleBlur('utilidad')"
                  @input="dropdownUtilidad = true"
                  placeholder="Buscar (ej. 3.4, Utilidad, Resultado)..."
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                >
                <!-- Dropdown Lista -->
                <ul v-if="dropdownUtilidad" class="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm">
                  <li v-if="cuentasFiltradasUtilidad.length === 0" class="text-gray-500 cursor-default select-none relative py-2 px-4">
                    No se encontraron cuentas
                  </li>
                  <li v-for="cuenta in cuentasFiltradasUtilidad" 
                      :key="cuenta.id" 
                      @mousedown="seleccionarUtilidad(cuenta)"
                      class="cursor-pointer select-none relative py-2 pl-3 pr-4 hover:bg-indigo-600 hover:text-white text-gray-900">
                    <span class="font-bold">{{ cuenta.codigo }}</span>
                    <span class="ml-2">{{ cuenta.nombre }}</span>
                  </li>
                </ul>
              </div>
            </div>

            <!-- 🔍 BÚSQUEDA: Utilidades Acumuladas -->
            <div class="relative">
              <label class="block text-gray-700 text-sm font-bold mb-1">Cuenta Utilidades/Pérdidas Acumuladas</label>
              <div class="relative rounded-md shadow-sm">
                <input 
                  type="text" 
                  v-model="busquedaAcumulada" 
                  @focus="dropdownAcumulada = true"
                  @blur="handleBlur('acumulada')"
                  @input="dropdownAcumulada = true"
                  placeholder="Buscar (ej. 3.3, Acumuladas)..."
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                >
                <!-- Dropdown Lista -->
                <ul v-if="dropdownAcumulada" class="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm">
                  <li v-if="cuentasFiltradasAcumulada.length === 0" class="text-gray-500 cursor-default select-none relative py-2 px-4">
                    No se encontraron cuentas
                  </li>
                  <li v-for="cuenta in cuentasFiltradasAcumulada" 
                      :key="cuenta.id" 
                      @mousedown="seleccionarAcumulada(cuenta)"
                      class="cursor-pointer select-none relative py-2 pl-3 pr-4 hover:bg-indigo-600 hover:text-white text-gray-900">
                    <span class="font-bold">{{ cuenta.codigo }}</span>
                    <span class="ml-2">{{ cuenta.nombre }}</span>
                  </li>
                </ul>
              </div>
            </div>

          </div>

          <div class="mt-6 flex justify-end space-x-3">
            <button @click="cerrarConfigModal" class="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400">Cancelar</button>
            <button 
              @click="guardarConfiguracion" 
              :disabled="cargandoConfig || !configForm.cuenta_utilidad_periodo_id || !configForm.cuenta_utilidades_acumuladas_id" 
              class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50">
              {{ cargandoConfig ? 'Guardando...' : 'Guardar Configuración' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue' // 🔹 Agregado computed
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

const authStore = useAuthStore()

// State General
const empresas = ref([])
const tenants = ref([])
const selectedTenantId = ref('')
const mostrarFormulario = ref(false)
const cargando = ref(false)
const cargandoLista = ref(false)
const error = ref('')
const successMsg = ref('')
const nuevaEmpresa = ref({ nombre: '', nit: '', direccion: '' })

// State Modal Configuración
const showConfigModal = ref(false)
const empresaConfig = ref(null)
const configForm = ref({ cuenta_utilidad_periodo_id: '', cuenta_utilidades_acumuladas_id: '' })
const cuentasPatrimonio = ref([])
const cargandoConfig = ref(false)
const errorConfig = ref('')
const successConfig = ref('')

// 🔹 NUEVO: Estado para los buscadores
const busquedaUtilidad = ref('')
const busquedaAcumulada = ref('')
const dropdownUtilidad = ref(false)
const dropdownAcumulada = ref(false)

// 🔹 NUEVO: Lógica de filtrado en tiempo real
const cuentasFiltradasUtilidad = computed(() => {
  const termino = busquedaUtilidad.value.toLowerCase()
  if (!termino) return cuentasPatrimonio.value
  return cuentasPatrimonio.value.filter(c => 
    c.nombre.toLowerCase().includes(termino) || c.codigo.toLowerCase().includes(termino)
  )
})

const cuentasFiltradasAcumulada = computed(() => {
  const termino = busquedaAcumulada.value.toLowerCase()
  if (!termino) return cuentasPatrimonio.value
  return cuentasPatrimonio.value.filter(c => 
    c.nombre.toLowerCase().includes(termino) || c.codigo.toLowerCase().includes(termino)
  )
})

// 🔹 Cargar lista de tenants solo si es superadmin
const fetchTenants = async () => {
  if (!authStore.isSuperAdmin) return
  try {
    const res = await api.get('/tenants/')
    tenants.value = res.data.filter(t => !['sistema', 'system', 'public'].includes(t.schema_name))
  } catch (err) { console.error('Error cargando tenants:', err) }
}

const cargarEmpresas = async () => {
  if (authStore.isSuperAdmin && !selectedTenantId.value) {
    empresas.value = []
    return
  }
  cargandoLista.value = true
  error.value = ''
  try {
    const params = authStore.isSuperAdmin ? { tenant_id: selectedTenantId.value } : {}
    const response = await api.get('/empresas/', { params })
    empresas.value = response.data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al cargar empresas'
  } finally {
    cargandoLista.value = false
  }
}

const handleTenantChange = () => {
  empresas.value = []
  cargarEmpresas()
}

const crearEmpresa = async () => {
  cargando.value = true; error.value = ''; successMsg.value = ''
  try {
    await api.post('/empresas/', {
      nombre: nuevaEmpresa.value.nombre,
      nit: nuevaEmpresa.value.nit,
      direccion: nuevaEmpresa.value.direccion
    })
    successMsg.value = '✅ Empresa creada exitosamente.'
    nuevaEmpresa.value = { nombre: '', nit: '', direccion: '' }
    mostrarFormulario.value = false
    await cargarEmpresas()
  } catch (err) {
    const detail = err.response?.data?.detail
    error.value = (err.response?.status === 403 && detail) ? detail : (detail || 'Error al crear empresa')
  } finally {
    cargando.value = false
  }
}

// 🔹 Abrir Modal con lógica de pre-llenado
const abrirConfiguracion = async (empresa) => {
  empresaConfig.value = empresa
  showConfigModal.value = true
  errorConfig.value = ''
  successConfig.value = ''
  cargandoConfig.value = true
  busquedaUtilidad.value = ''
  busquedaAcumulada.value = ''
  dropdownUtilidad.value = false
  dropdownAcumulada.value = false

  try {
    const params = authStore.isSuperAdmin && selectedTenantId.value ? { tenant_id: selectedTenantId.value } : {}

    // 1. Cargar plan de cuentas
    const resCuentas = await api.get('/plan-cuentas/', { params: { ...params, empresa_id: empresa.id } })
    cuentasPatrimonio.value = resCuentas.data.filter(c => c.tipo === 'patrimonio' && c.activa)

    // 2. Cargar configuración actual
    const resEmpresa = await api.get(`/empresas/${empresa.id}`, { params })
    const data = resEmpresa.data
    configForm.value = {
      cuenta_utilidad_periodo_id: data.cuenta_utilidad_periodo_id || '',
      cuenta_utilidades_acumuladas_id: data.cuenta_utilidades_acumuladas_id || ''
    }

    // 3. Pre-llenar los inputs de búsqueda si ya hay selección
    if (configForm.value.cuenta_utilidad_periodo_id) {
      const c = cuentasPatrimonio.value.find(c => c.id === configForm.value.cuenta_utilidad_periodo_id)
      if (c) busquedaUtilidad.value = `${c.codigo} - ${c.nombre}`
    }
    if (configForm.value.cuenta_utilidades_acumuladas_id) {
      const c = cuentasPatrimonio.value.find(c => c.id === configForm.value.cuenta_utilidades_acumuladas_id)
      if (c) busquedaAcumulada.value = `${c.codigo} - ${c.nombre}`
    }

  } catch (err) {
    errorConfig.value = err.response?.data?.detail || 'Error al cargar datos para configuración'
  } finally {
    cargandoConfig.value = false
  }
}

// 🔹 Métodos de selección del dropdown
const seleccionarUtilidad = (cuenta) => {
  configForm.value.cuenta_utilidad_periodo_id = cuenta.id
  busquedaUtilidad.value = `${cuenta.codigo} - ${cuenta.nombre}`
  dropdownUtilidad.value = false
}

const seleccionarAcumulada = (cuenta) => {
  configForm.value.cuenta_utilidades_acumuladas_id = cuenta.id
  busquedaAcumulada.value = `${cuenta.codigo} - ${cuenta.nombre}`
  dropdownAcumulada.value = false
}

// Manejo de blur para cerrar dropdowns (con delay para permitir clic)
const handleBlur = (tipo) => {
  setTimeout(() => {
    if (tipo === 'utilidad') dropdownUtilidad.value = false
    else dropdownAcumulada.value = false
  }, 200)
}

const guardarConfiguracion = async () => {
  cargandoConfig.value = true; errorConfig.value = ''; successConfig.value = ''
  try {
    const params = authStore.isSuperAdmin && selectedTenantId.value ? { tenant_id: selectedTenantId.value } : {}
    
    const payload = {
      cuenta_utilidad_periodo_id: configForm.value.cuenta_utilidad_periodo_id || null,
      cuenta_utilidades_acumuladas_id: configForm.value.cuenta_utilidades_acumuladas_id || null
    }

    await api.put(`/empresas/${empresaConfig.value.id}`, payload, { params })
    successConfig.value = '✅ Configuración guardada correctamente.'
    
    await cargarEmpresas()
    setTimeout(() => cerrarConfigModal(), 1000) // Cerrar modal tras éxito
  } catch (err) {
    errorConfig.value = err.response?.data?.detail || 'Error al guardar configuración'
  } finally {
    cargandoConfig.value = false
  }
}

const cerrarConfigModal = () => {
  showConfigModal.value = false
  empresaConfig.value = null
  configForm.value = { cuenta_utilidad_periodo_id: '', cuenta_utilidades_acumuladas_id: '' }
}

onMounted(async () => {
  await fetchTenants()
  if (authStore.isSuperAdmin && tenants.value.length > 0) {
    selectedTenantId.value = tenants.value[0].id
  }
  await cargarEmpresas()
})
</script>