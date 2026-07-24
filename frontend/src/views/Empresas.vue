<!-- src/views/Empresas.vue -->
<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-7xl mx-auto space-y-6">
      <!-- Header -->
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-3xl font-bold text-gray-800 mb-1">Empresas</h1>
          <p class="text-gray-600">
            <template v-if="authStore.isSuperAdmin && superAdminStore.currentTenantId">
              Gestionando empresas de: <span class="font-semibold text-blue-600">{{ superAdminStore.currentTenant?.name }}</span>
            </template>
            <template v-else>
              Gestiona las empresas de tu firma contable
            </template>
          </p>
        </div>
        <button
          v-if="!authStore.isSuperAdmin || superAdminStore.currentTenantId"
          @click="abrirModalCrear"
          class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2.5 rounded-lg font-medium transition-colors flex items-center gap-2 shadow-sm"
        >
          <Plus class="w-5 h-5" />
          Nueva Empresa
        </button>
      </div>

      <!-- Selector de Contexto (Solo Superadmin) -->
      <SuperAdminContextSelector v-if="authStore.isSuperAdmin" />

      <!-- Mensajes -->
      <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg flex justify-between items-center">
        <span>{{ error }}</span>
        <button @click="error = ''" class="text-sm underline hover:no-underline">Cerrar</button>
      </div>
      <div v-if="successMsg" class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-lg flex justify-between items-center">
        <span>{{ successMsg }}</span>
        <button @click="successMsg = ''" class="text-sm underline hover:no-underline">Cerrar</button>
      </div>

      <!-- Estado vacío para superadmin sin contexto -->
      <div v-if="authStore.isSuperAdmin && !superAdminStore.currentTenantId" class="bg-white rounded-lg shadow p-12 text-center border border-gray-200">
        <svg class="mx-auto h-16 w-16 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
        <p class="mt-4 text-gray-500 text-lg">Seleccione una firma en el filtro superior para visualizar sus empresas.</p>
      </div>

      <!-- Contenido principal -->
      <div v-else class="space-y-6">
        <!-- Loading -->
        <div v-if="cargandoLista" class="text-center py-12">
          <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p class="mt-2 text-gray-500">Cargando empresas...</p>
        </div>

        <!-- Empty State -->
        <div v-else-if="empresas.length === 0" class="bg-white rounded-lg shadow p-12 text-center border border-gray-200">
          <svg class="mx-auto h-16 w-16 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
          <p class="mt-4 text-gray-500 text-lg">No hay empresas registradas</p>
          <button
            v-if="!authStore.isSuperAdmin || superAdminStore.currentTenantId"
            @click="abrirModalCrear"
            class="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
          >
            Crear Primera Empresa
          </button>
        </div>

        <!-- Listado de empresas -->
        <div v-else class="bg-white shadow-md rounded-lg overflow-hidden">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">NIT</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Régimen</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado Cierre</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <template v-for="empresa in empresas" :key="empresa.id">
                <!-- Fila principal de la empresa -->
                <tr class="hover:bg-gray-50">
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm font-medium text-gray-900">{{ empresa.nombre }}</div>
                    <div v-if="empresa.nombre_comercial" class="text-xs text-gray-500">{{ empresa.nombre_comercial }}</div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ empresa.nit }}</td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ empresa.regimen_fiscal?.nombre || '-' }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm">
                    <span v-if="empresa.cuenta_utilidad_periodo_id && empresa.cuenta_utilidades_acumuladas_id" class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                      ✅ Configurada
                    </span>
                    <span v-else class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">
                      ⚠️ Pendiente
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm">
                    <span v-if="empresa.is_active" class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                      Activa
                    </span>
                    <span v-else class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                      Inactiva
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-right space-x-2">
                    <button @click="abrirModalEditar(empresa)" class="text-blue-600 hover:text-blue-900 font-medium">Editar</button>
                    <button @click="abrirConfiguracion(empresa)" class="text-green-600 hover:text-green-900 font-medium">Configurar</button>
                    <button @click="empresaExpandida = empresaExpandida?.id === empresa.id ? null : empresa" class="text-purple-600 hover:text-purple-900 font-medium">
                      {{ empresaExpandida?.id === empresa.id ? 'Ocultar' : 'Domicilios' }}
                    </button>
                    <button v-if="empresa.is_active" @click="confirmarEliminar(empresa)" class="text-red-600 hover:text-red-900 font-medium">Desactivar</button>
                    <button @click="empresaExpandidaRep = empresaExpandidaRep?.id === empresa.id ? null : empresa" class="text-indigo-600 hover:text-indigo-900 font-medium">
                      {{ empresaExpandidaRep?.id === empresa.id ? 'Ocultar' : 'Representantes' }}
                    </button>
                  </td>
                </tr>
                <!-- Fila expandible de domicilios -->
                <tr v-if="empresaExpandida?.id === empresa.id">
                  <td colspan="6" class="px-6 py-4 bg-gray-50 border-t border-gray-200">
                    <DomicilioManager :empresa-id="empresa.id" :tenant-id="currentTenantIdForComponents" @updated="cargarEmpresas" />
                  </td>
                </tr>
                <!-- Fila expandible de representantes legales -->
                <tr v-if="empresaExpandidaRep?.id === empresa.id">
                  <td colspan="6" class="px-6 py-4 bg-gray-50 border-t border-gray-200">
                    <RepresentanteManager :empresa-id="empresa.id" :tenant-id="currentTenantIdForComponents" @updated="cargarEmpresas" />
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 🔹 MODAL CREAR/EDITAR EMPRESA -->
      <div v-if="showModalEmpresa" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center z-50">
        <div class="bg-white p-6 rounded-lg shadow-xl max-w-2xl w-full mx-4 relative max-h-[90vh] overflow-y-auto">
          <button @click="cerrarModalEmpresa" class="absolute top-4 right-4 text-gray-400 hover:text-gray-600">✕</button>
          <h3 class="text-xl font-bold mb-4 text-gray-800 pr-6">
            {{ modoEdicion ? 'Editar Empresa' : 'Nueva Empresa' }}
          </h3>
          <div v-if="errorModal" class="bg-red-100 border border-red-400 text-red-700 px-3 py-2 rounded mb-4 text-sm">
            {{ errorModal }}
          </div>
          <form @submit.prevent="guardarEmpresa" class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <!-- NIT -->
              <div>
                <label class="block text-gray-700 text-sm font-bold mb-1">NIT *</label>
                <div class="relative">
                  <input
                    v-model="formEmpresa.nit"
                    @input="debounceValidarNit"
                    @blur="validarNitEnTiempoReal(formEmpresa.nit)"
                    type="text"
                    class="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    :class="{
                      'border-green-500': nitValido && formEmpresa.nit,
                      'border-red-500': !nitValido && formEmpresa.nit
                    }"
                    placeholder="1234567-8"
                    required
                  />
                  <div v-if="validandoNit" class="absolute right-3 top-2.5">
                    <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                  </div>
                </div>
                <p v-if="nitMensaje" class="text-xs mt-1" :class="nitValido ? 'text-green-600' : 'text-red-600'">
                  {{ nitMensaje }}
                </p>
                <p v-else class="text-xs text-gray-500 mt-1">Formato: 1234567-8</p>
              </div>

              <!-- Nombre Comercial -->
              <div>
                <label class="block text-gray-700 text-sm font-bold mb-1">Nombre Comercial</label>
                <input
                  v-model="formEmpresa.nombre_comercial"
                  type="text"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <!-- Razón Social -->
              <div class="md:col-span-2">
                <label class="block text-gray-700 text-sm font-bold mb-1">Razón Social (Nombre) *</label>
                <input
                  v-model="formEmpresa.nombre"
                  type="text"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>

              <!-- Fecha Constitución -->
              <div>
                <label class="block text-gray-700 text-sm font-bold mb-1">Fecha de Constitución</label>
                <input
                  v-model="formEmpresa.fecha_constitucion_display"
                  type="text"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="dd/mm/yyyy"
                  @input="formatearFecha"
                  maxlength="10"
                />
                <p class="text-xs text-gray-500 mt-1">Formato: dd/mm/yyyy</p>
              </div>

              <!-- 🆕 Régimen Fiscal (Dropdown simple) -->
              <div>
                <label class="block text-gray-700 text-sm font-bold mb-1">Régimen Fiscal</label>
                <select
                  v-model="formEmpresa.regimen_fiscal_id"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                >
                  <option :value="null">-- Seleccionar --</option>
                  <option v-for="regimen in regimenes" :key="regimen.id" :value="regimen.id">
                    {{ regimen.codigo }} - {{ regimen.nombre }}
                  </option>
                </select>
              </div>

              <!-- 🆕 Tipo de Persona (Dropdown simple) -->
              <div>
                <label class="block text-gray-700 text-sm font-bold mb-1">Tipo de Persona</label>
                <select
                  v-model="formEmpresa.tipo_persona_id"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                >
                  <option :value="null">-- Seleccionar --</option>
                  <option v-for="tipo in tiposPersona" :key="tipo.id" :value="tipo.id">
                    {{ tipo.nombre }}
                  </option>
                </select>
              </div>

              <!-- Actividad Económica (Buscador con dropdown, se mantiene) -->
              <div class="md:col-span-2 relative">
                <label class="block text-gray-700 text-sm font-bold mb-1">Actividad Económica</label>
                <input
                  v-model="busquedaActividad"
                  @focus="dropdownActividad = true"
                  @blur="handleBlurActividad"
                  @input="dropdownActividad = true"
                  placeholder="Buscar actividad económica..."
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <ul v-if="dropdownActividad" class="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm">
                  <li v-if="actividadesFiltradas.length === 0" class="text-gray-500 cursor-default select-none relative py-2 px-4">
                    No se encontraron actividades
                  </li>
                  <li v-for="act in actividadesFiltradas"
                      :key="act.id"
                      @mousedown="seleccionarActividad(act)"
                      class="cursor-pointer select-none relative py-2 pl-3 pr-4 hover:bg-indigo-600 hover:text-white text-gray-900">
                    <span class="font-bold">{{ act.codigo_sat }}</span>
                    <span class="ml-2">{{ act.nombre_actividad }}</span>
                  </li>
                </ul>
              </div>
            </div>

            <div class="flex justify-end space-x-3 pt-4 border-t">
              <button
                type="button"
                @click="cerrarModalEmpresa"
                class="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition"
              >
                Cancelar
              </button>
              <button
                type="submit"
                :disabled="cargandoModal"
                class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition"
              >
                {{ cargandoModal ? 'Guardando...' : (modoEdicion ? 'Actualizar' : 'Crear') }}
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- 🔹 MODAL DE CONFIGURACIÓN DE CUENTAS -->
      <div v-if="showConfigModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center z-50">
        <div class="bg-white p-6 rounded-lg shadow-xl max-w-lg w-full mx-4 relative">
          <button @click="cerrarConfigModal" class="absolute top-4 right-4 text-gray-400 hover:text-gray-600">✕</button>
          <h3 class="text-lg font-bold mb-4 text-gray-800 pr-6">Configurar Cuentas de Cierre</h3>
          <p class="text-sm text-gray-500 mb-4">Empresa: <span class="font-medium">{{ empresaConfig?.nombre }}</span></p>
          <div v-if="errorConfig" class="bg-red-100 border border-red-400 text-red-700 px-3 py-2 rounded mb-4 text-sm">{{ errorConfig }}</div>
          <div v-if="successConfig" class="bg-green-100 border border-green-400 text-green-700 px-3 py-2 rounded mb-4 text-sm">{{ successConfig }}</div>
          
          <div class="space-y-5">
            <!-- Búsqueda: Utilidad del Período -->
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
                />
                <ul v-if="dropdownUtilidad" class="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm">
                  <li v-if="cuentasFiltradasUtilidad.length === 0" class="text-gray-500 cursor-default select-none relative py-2 px-4">No se encontraron cuentas</li>
                  <li v-for="cuenta in cuentasFiltradasUtilidad" :key="cuenta.id" @mousedown="seleccionarUtilidad(cuenta)" class="cursor-pointer select-none relative py-2 pl-3 pr-4 hover:bg-indigo-600 hover:text-white text-gray-900">
                    <span class="font-bold">{{ cuenta.codigo }}</span>
                    <span class="ml-2">{{ cuenta.nombre }}</span>
                  </li>
                </ul>
              </div>
            </div>

            <!-- Búsqueda: Utilidades Acumuladas -->
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
                />
                <ul v-if="dropdownAcumulada" class="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm">
                  <li v-if="cuentasFiltradasAcumulada.length === 0" class="text-gray-500 cursor-default select-none relative py-2 px-4">No se encontraron cuentas</li>
                  <li v-for="cuenta in cuentasFiltradasAcumulada" :key="cuenta.id" @mousedown="seleccionarAcumulada(cuenta)" class="cursor-pointer select-none relative py-2 pl-3 pr-4 hover:bg-indigo-600 hover:text-white text-gray-900">
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
              class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {{ cargandoConfig ? 'Guardando...' : 'Guardar Configuración' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useCompanyStore } from '@/stores/company'
import { useSuperAdminStore } from '@/stores/superAdmin'
import { Plus } from '@lucide/vue'
import api from '@/services/api'
import DomicilioManager from '@/components/empresas/DomicilioManager.vue'
import RepresentanteManager from '@/components/empresas/RepresentanteManager.vue'
import SuperAdminContextSelector from '@/components/SuperAdminContextSelector.vue'

const authStore = useAuthStore()
const companyStore = useCompanyStore()
const superAdminStore = useSuperAdminStore()

// Estado para empresa expandida (domicilios y representantes)
const empresaExpandida = ref(null)
const empresaExpandidaRep = ref(null)

// State General
const empresas = ref([])
const cargandoLista = ref(false)
const error = ref('')
const successMsg = ref('')

// Validación NIT
const nitValido = ref(true)
const nitMensaje = ref('')
const validandoNit = ref(false)

// State Modal Empresa
const showModalEmpresa = ref(false)
const modoEdicion = ref(false)
const empresaEditando = ref(null)
const cargandoModal = ref(false)
const cargandoCatalogos = ref(false)
const errorModal = ref('')

const formEmpresa = ref({
  nit: '',
  nombre: '',
  razon_social: '',
  nombre_comercial: '',
  fecha_constitucion: '',
  fecha_constitucion_display: '',
  regimen_fiscal_id: '',
  tipo_persona_id: '',
  actividad_economica_id: ''
})

// Catálogos
const regimenes = ref([])
const tiposPersona = ref([])
const actividadesEconomicas = ref([])

// 🆕 Dropdowns con búsqueda (SOLO para Actividad Económica)
const busquedaActividad = ref('')
const dropdownActividad = ref(false)

// Debounce manual para NIT
let debounceTimerNit = null
const debounceValidarNit = () => {
  clearTimeout(debounceTimerNit)
  debounceTimerNit = setTimeout(() => {
    const nit = formEmpresa.value.nit
    if (nit && nit.length >= 7) {
      validarNitEnTiempoReal(nit)
    }
  }, 500)
}

// 🆕 Computed para filtrado (SOLO para Actividad Económica)
const actividadesFiltradas = computed(() => {
  const termino = busquedaActividad.value.toLowerCase()
  if (!termino) return actividadesEconomicas.value
  return actividadesEconomicas.value.filter(a =>
    a.nombre_actividad.toLowerCase().includes(termino) ||
    (a.codigo_sat && a.codigo_sat.toLowerCase().includes(termino))
  )
})

// ⭐ Computed: tenant_id para componentes hijos
const currentTenantIdForComponents = computed(() => {
  if (authStore.isSuperAdmin) {
    return superAdminStore.currentTenantId || null
  }
  return authStore.tenantId || null
})

// Validación de NIT en tiempo real
const validarNitEnTiempoReal = async (nit) => {
  if (!nit || nit.length < 7) {
    nitValido.value = true
    nitMensaje.value = ''
    return
  }
  validandoNit.value = true
  try {
    const params = authStore.isSuperAdmin && superAdminStore.currentTenantId
      ? { tenant_id: superAdminStore.currentTenantId }
      : {}
    await api.post('/empresas/validar-nit', { nit }, { params })
    nitValido.value = true
    nitMensaje.value = '✅ NIT válido y disponible'
  } catch (err) {
    nitValido.value = false
    const detail = err.response?.data?.detail || ''
    if (err.response?.status === 400) {
      nitMensaje.value = `❌ ${detail}`
    } else if (err.response?.status === 409) {
      nitMensaje.value = `❌ ${detail}`
    } else {
      nitMensaje.value = '⚠️ No se pudo validar el NIT'
    }
  } finally {
    validandoNit.value = false
  }
}

// State Modal Configuración
const showConfigModal = ref(false)
const empresaConfig = ref(null)
const configForm = ref({ cuenta_utilidad_periodo_id: '', cuenta_utilidades_acumuladas_id: '' })
const cuentasPatrimonio = ref([])
const cargandoConfig = ref(false)
const errorConfig = ref('')
const successConfig = ref('')
const busquedaUtilidad = ref('')
const busquedaAcumulada = ref('')
const dropdownUtilidad = ref(false)
const dropdownAcumulada = ref(false)

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

// ============================================
// Cargar catálogos
// ============================================
const cargarCatalogos = async () => {
  cargandoCatalogos.value = true
  try {
    const [resRegimenes, resTipos, resActividades] = await Promise.all([
      api.get('/regimenes-fiscales/activos'),
      api.get('/tipos-persona/lista'),
      api.get('/actividades-economicas/activas')
    ])
    regimenes.value = (resRegimenes.data || []).filter(r => r.is_active !== false && r.activo !== false)
    tiposPersona.value = resTipos.data || []
    actividadesEconomicas.value = (resActividades.data || []).filter(a => a.activa !== false && a.is_active !== false)
  } catch (err) {
    console.error('❌ Error cargando catálogos:', err)
  } finally {
    cargandoCatalogos.value = false
  }
}

// ============================================
// Formatear fecha dd/mm/yyyy
// ============================================
const formatearFecha = (event) => {
  let value = event.target.value.replace(/\D/g, '')
  if (value.length >= 2) {
    value = value.substring(0, 2) + '/' + value.substring(2)
  }
  if (value.length >= 5) {
    value = value.substring(0, 5) + '/' + value.substring(5, 9)
  }
  formEmpresa.value.fecha_constitucion_display = value
  if (value.length === 10) {
    const [dia, mes, anio] = value.split('/')
    formEmpresa.value.fecha_constitucion = `${anio}-${mes}-${dia}`
  } else {
    formEmpresa.value.fecha_constitucion = ''
  }
}

// ============================================
// Selección de dropdowns (SOLO Actividad Económica)
// ============================================
const seleccionarActividad = (act) => {
  formEmpresa.value.actividad_economica_id = act.id
  busquedaActividad.value = `${act.codigo_sat || ''} - ${act.nombre_actividad}`.replace(/^ - /, '')
  dropdownActividad.value = false
}

const handleBlurActividad = () => {
  setTimeout(() => { dropdownActividad.value = false }, 200)
}

// ============================================
// Cargar Empresas
// ============================================
const cargarEmpresas = async () => {
  if (authStore.isSuperAdmin && !superAdminStore.currentTenantId) {
    empresas.value = []
    return
  }
  cargandoLista.value = true
  error.value = ''
  try {
    if (authStore.isSuperAdmin) {
      const params = { tenant_id: superAdminStore.currentTenantId }
      const resp = await api.get('/empresas/', { params })
      empresas.value = resp.data
    } else {
      if (!companyStore.hasCompanies) {
        try {
          await companyStore.loadCompanies()
        } catch (err) {
          console.warn('No se pudieron cargar empresas:', err)
        }
      }
      empresas.value = companyStore.availableCompanies || []
    }
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al cargar empresas'
    empresas.value = []
  } finally {
    cargandoLista.value = false
  }
}

watch(
  () => superAdminStore.currentTenantId,
  (newTenantId, oldTenantId) => {
    if (newTenantId !== oldTenantId) {
      empresaExpandida.value = null
      empresaExpandidaRep.value = null
      cargarEmpresas()
    }
  }
)

watch(() => companyStore.availableCompanies, (newCompanies) => {
  if (!authStore.isSuperAdmin) {
    empresas.value = newCompanies
  }
}, { immediate: true })

// ============================================
// Modal Crear
// ============================================
const abrirModalCrear = async () => {
  if (authStore.isSuperAdmin && !superAdminStore.currentTenantId) {
    error.value = 'Debe seleccionar un tenant antes de crear una empresa'
    return
  }
  modoEdicion.value = false
  empresaEditando.value = null
  formEmpresa.value = {
    nit: '',
    nombre: '',
    razon_social: '',
    nombre_comercial: '',
    fecha_constitucion: '',
    fecha_constitucion_display: '',
    regimen_fiscal_id: '',
    tipo_persona_id: '',
    actividad_economica_id: ''
  }
  busquedaActividad.value = '' // 🆕 Solo limpiamos este
  nitValido.value = true
  nitMensaje.value = ''
  errorModal.value = ''
  showModalEmpresa.value = true
  await cargarCatalogos()
}

// ============================================
// Modal Editar
// ============================================
const abrirModalEditar = async (empresa) => {
  modoEdicion.value = true
  empresaEditando.value = empresa
  let fechaDisplay = ''
  if (empresa.fecha_constitucion) {
    const [anio, mes, dia] = empresa.fecha_constitucion.split('-')
    if (anio && mes && dia) {
      fechaDisplay = `${dia}/${mes}/${anio}`
    }
  }
  formEmpresa.value = {
    nit: empresa.nit || '',
    nombre: empresa.nombre || '',
    razon_social: empresa.razon_social || '',
    nombre_comercial: empresa.nombre_comercial || '',
    fecha_constitucion: empresa.fecha_constitucion || '',
    fecha_constitucion_display: fechaDisplay,
    regimen_fiscal_id: empresa.regimen_fiscal_id || '',
    tipo_persona_id: empresa.tipo_persona_id || '',
    actividad_economica_id: empresa.actividad_economica_id || ''
  }
  errorModal.value = ''
  nitValido.value = true
  nitMensaje.value = ''
  showModalEmpresa.value = true
  await cargarCatalogos()
  
  // 🆕 Solo necesitamos restaurar el texto de búsqueda para Actividad Económica
  if (empresa.actividad_economica_id) {
    const a = actividadesEconomicas.value.find(a => a.id === empresa.actividad_economica_id)
    if (a) busquedaActividad.value = `${a.codigo_sat || ''} - ${a.nombre_actividad}`.replace(/^ - /, '')
  }
}

const cerrarModalEmpresa = () => {
  showModalEmpresa.value = false
  empresaEditando.value = null
  errorModal.value = ''
}

// ============================================
// Guardar Empresa
// ============================================
const guardarEmpresa = async () => {
  if (!nitValido.value && formEmpresa.value.nit) {
    errorModal.value = 'El NIT ingresado no es válido o ya está en uso.'
    return
  }
  
  console.log('🔹 Iniciando guardado...')
  console.log('🔹 formEmpresa:', formEmpresa.value)
  console.log('🔹 modoEdicion:', modoEdicion.value)
  console.log('🔹 isSuperAdmin:', authStore.isSuperAdmin)
  
  cargandoModal.value = true
  errorModal.value = ''
  
  try {
    const payload = {
      nit: formEmpresa.value.nit,
      nombre: formEmpresa.value.nombre,
      razon_social: formEmpresa.value.razon_social || null,
      nombre_comercial: formEmpresa.value.nombre_comercial || null,
      fecha_constitucion: formEmpresa.value.fecha_constitucion || null,
      regimen_fiscal_id: formEmpresa.value.regimen_fiscal_id || null,
      tipo_persona_id: formEmpresa.value.tipo_persona_id || null,
      actividad_economica_id: formEmpresa.value.actividad_economica_id || null
    }
    
    console.log('🔹 Payload a enviar:', payload)
    
    const params = authStore.isSuperAdmin && superAdminStore.currentTenantId
      ? { tenant_id: superAdminStore.currentTenantId }
      : {}
    
    console.log('🔹 Params:', params)
    
    if (modoEdicion.value && empresaEditando.value) {
      console.log('🔹 Actualizando empresa ID:', empresaEditando.value.id)
      await api.put(`/empresas/${empresaEditando.value.id}`, payload, { params })
      successMsg.value = '✅ Empresa actualizada exitosamente'
    } else {
      console.log('🔹 Creando nueva empresa...')
      await api.post('/empresas/', payload, { params })
      successMsg.value = '✅ Empresa creada exitosamente'
    }
    
    console.log('✅ Empresa guardada exitosamente')
    cerrarModalEmpresa()
    await cargarEmpresas()
  } catch (err) {
    console.error('❌ Error al guardar empresa:', err)
    console.error('❌ Response:', err.response?.data)
    const detail = err.response?.data?.detail
    errorModal.value = (err.response?.status === 403 && detail) ? detail : (detail || 'Error al guardar empresa')
  } finally {
    cargandoModal.value = false
  }
}

// ============================================
// Eliminar (Soft Delete)
// ============================================
const confirmarEliminar = (empresa) => {
  if (confirm(`¿Está seguro de desactivar la empresa "${empresa.nombre}"?`)) {
    eliminarEmpresa(empresa)
  }
}

const eliminarEmpresa = async (empresa) => {
  try {
    const params = authStore.isSuperAdmin && superAdminStore.currentTenantId
      ? { tenant_id: superAdminStore.currentTenantId }
      : {}
    await api.delete(`/empresas/${empresa.id}`, { params })
    successMsg.value = '✅ Empresa desactivada exitosamente'
    await cargarEmpresas()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al desactivar empresa'
  }
}

// ============================================
// Configuración de cuentas
// ============================================
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
    const params = authStore.isSuperAdmin && superAdminStore.currentTenantId
      ? { tenant_id: superAdminStore.currentTenantId }
      : {}
    const resCuentas = await api.get('/plan-cuentas/', { params: { ...params, empresa_id: empresa.id } })
    cuentasPatrimonio.value = resCuentas.data.filter(c => c.tipo === 'patrimonio' && c.activa)
    const resEmpresa = await api.get(`/empresas/${empresa.id}`, { params })
    const data = resEmpresa.data
    configForm.value = {
      cuenta_utilidad_periodo_id: data.cuenta_utilidad_periodo_id || '',
      cuenta_utilidades_acumuladas_id: data.cuenta_utilidades_acumuladas_id || ''
    }
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

const handleBlur = (tipo) => {
  setTimeout(() => {
    if (tipo === 'utilidad') dropdownUtilidad.value = false
    else dropdownAcumulada.value = false
  }, 200)
}

const guardarConfiguracion = async () => {
  cargandoConfig.value = true
  errorConfig.value = ''
  successConfig.value = ''
  try {
    const params = authStore.isSuperAdmin && superAdminStore.currentTenantId
      ? { tenant_id: superAdminStore.currentTenantId }
      : {}
    const payload = {
      cuenta_utilidad_periodo_id: configForm.value.cuenta_utilidad_periodo_id || null,
      cuenta_utilidades_acumuladas_id: configForm.value.cuenta_utilidades_acumuladas_id || null
    }
    await api.put(`/empresas/${empresaConfig.value.id}`, payload, { params })
    successConfig.value = '✅ Configuración guardada correctamente.'
    await cargarEmpresas()
    setTimeout(() => cerrarConfigModal(), 1000)
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

// ============================================
// Inicialización
// ============================================
onMounted(async () => {
  if (!authStore.isSuperAdmin) {
    await cargarEmpresas()
  }
})
</script>