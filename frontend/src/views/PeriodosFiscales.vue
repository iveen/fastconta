<!-- src/views/PeriodosFiscales.vue -->
<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-6xl mx-auto space-y-6">
      <div class="flex justify-between items-center">
        <h2 class="text-2xl font-bold text-gray-800">Períodos Fiscales</h2>
        <button
          @click="mostrarForm = !mostrarForm"
          :disabled="!companyStore.selectedCompanyId"
          class="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600 transition disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {{ mostrarForm ? 'Cancelar' : 'Nuevo Período' }}
        </button>
      </div>

      <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">{{ error }}</div>
      <div v-if="exito" class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">{{ exito }}</div>

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

      <!-- ✅ MENSAJE SI NO HAY EMPRESA SELECCIONADA -->
      <div v-if="!companyStore.selectedCompanyId" class="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-12 rounded-lg text-center">
        <svg class="w-12 h-12 mx-auto mb-3 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
        <p class="text-lg font-semibold">Selecciona una empresa desde la barra superior para gestionar los períodos fiscales</p>
      </div>

      <!-- ✅ Formulario de creación (solo si hay empresa seleccionada) -->
      <div v-if="mostrarForm && companyStore.selectedCompanyId" class="bg-white shadow-md rounded-lg p-6">
        <h3 class="text-lg font-semibold mb-4">Nuevo Período Fiscal</h3>
        <form @submit.prevent="crearPeriodo">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label class="block text-gray-700 text-sm font-bold mb-2">Empresa</label>
              <input :value="companyStore.currentCompany?.nombre" disabled class="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-100 text-gray-700" />
            </div>
            <div>
              <label class="block text-gray-700 text-sm font-bold mb-2">Nombre</label>
              <input
                v-model="nuevoPeriodo.nombre"
                type="text"
                placeholder="Ej: 2026"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label class="block text-gray-700 text-sm font-bold mb-2">Fecha Inicio</label>
              <input
                v-model="nuevoPeriodo.fecha_inicio"
                type="date"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label class="block text-gray-700 text-sm font-bold mb-2">Fecha Fin</label>
              <input
                v-model="nuevoPeriodo.fecha_fin"
                type="date"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
          </div>
          <button
            type="submit"
            :disabled="cargando"
            class="bg-green-500 text-white px-6 py-2 rounded-md hover:bg-green-600 transition disabled:opacity-50"
          >
            {{ cargando ? 'Creando...' : 'Crear Período' }}
          </button>
        </form>
      </div>

      <!-- ✅ Listado de períodos (solo si hay empresa seleccionada) -->
      <div v-else-if="companyStore.selectedCompanyId">
        <div v-if="cargandoLista" class="text-center py-8 text-gray-500">Cargando...</div>
        <div v-else-if="periodos.length === 0" class="bg-white shadow-md rounded-lg p-8 text-center text-gray-500">
          No hay períodos fiscales registrados para esta empresa.
        </div>
        <div v-else class="bg-white shadow-md rounded-lg overflow-hidden">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nombre</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fecha Inicio</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fecha Fin</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Acciones</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="per in periodos" :key="per.id" class="hover:bg-gray-50">
                <td class="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">{{ per.nombre }}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">{{ per.fecha_inicio }}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">{{ per.fecha_fin }}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm">
                  <span :class="per.cerrado ? 'text-red-600' : 'text-green-600'">
                    {{ per.cerrado ? 'Cerrado' : 'Abierto' }}
                  </span>
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-sm">
                  <button
                    v-if="per.cerrado && puedeRevertirCierre"
                    @click="revertirCierre(per.id)"
                    :disabled="cargando"
                    class="text-orange-600 hover:text-orange-800 font-medium text-xs border border-orange-300 rounded px-3 py-1.5 hover:bg-orange-50 transition disabled:opacity-50 flex items-center gap-1"
                    title="Revertir cierre (Solo Admin/Superadmin)"
                  >
                    <span>🔄</span> Revertir Cierre
                  </button>
                  <span
                    v-else-if="per.cerrado && !puedeRevertirCierre"
                    class="text-gray-400 text-xs italic flex items-center gap-1"
                    title="Solo el Administrador de la Firma o el Superadmin pueden realizar esta acción"
                  >
                    🔒 Solo Administradores
                  </span>
                  <span v-else class="text-gray-400 text-xs">-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useCompanyStore } from '@/stores/company'  // ✅ NUEVO
import { formatFastApiError } from '@/utils/errorHandler'

const authStore = useAuthStore()
const companyStore = useCompanyStore()  // ✅ NUEVO

const tenants = ref([])
const selectedTenantId = ref('')
const periodos = ref([])
const mostrarForm = ref(false)
const cargando = ref(false)
const cargandoLista = ref(false)
const error = ref('')
const exito = ref('')
const nuevoPeriodo = ref({
  nombre: '',
  fecha_inicio: '',
  fecha_fin: ''
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

const handleTenantChange = () => {
  periodos.value = []
}

// ✅ CORRECCIÓN: Cargar períodos usando companyStore
const cargarPeriodos = async () => {
  if (!companyStore.selectedCompanyId) {
    periodos.value = []
    return
  }

  cargandoLista.value = true
  error.value = ''

  try {
    const params = {}
    if (authStore.isSuperAdmin && selectedTenantId.value) {
      params.tenant_id = selectedTenantId.value
    }
    // ✅ El interceptor ya inyecta X-Company-Id automáticamente
    const resp = await api.get('/periodos-fiscales/', { params })
    periodos.value = resp.data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al cargar períodos'
  } finally {
    cargandoLista.value = false
  }
}

// ✅ CORRECCIÓN: Crear período usando companyStore
const crearPeriodo = async () => {
  if (!companyStore.selectedCompanyId) {
    error.value = 'Debes seleccionar una empresa antes de crear un período.'
    return
  }

  cargando.value = true
  error.value = ''
  exito.value = ''

  try {
    await api.post('/periodos-fiscales/', {
      nombre: nuevoPeriodo.value.nombre,
      fecha_inicio: nuevoPeriodo.value.fecha_inicio,
      fecha_fin: nuevoPeriodo.value.fecha_fin,
      empresa_id: companyStore.selectedCompanyId  // ✅ Usar empresa del contexto global
    })
    exito.value = 'Período creado correctamente.'
    nuevoPeriodo.value = { nombre: '', fecha_inicio: '', fecha_fin: '' }
    mostrarForm.value = false
    await cargarPeriodos()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al crear período'
  } finally {
    cargando.value = false
  }
}

const puedeRevertirCierre = computed(() => {
  const user = authStore.user || {}
  const role = user.role || user.rol || {}
  const roleCode = role.codigo || role.code || authStore.roleCode || authStore.rol
  const codigoLimpio = String(role || '').toLowerCase().trim()
  return codigoLimpio === 'superadmin' || codigoLimpio === 'tenant_manager'
})

// ✅ CORRECCIÓN: Revertir cierre usando companyStore
const revertirCierre = async (periodoId) => {
  if (!puedeRevertirCierre.value) {
    error.value = "⛔ No tienes permisos para revertir un cierre contable."
    return
  }

  if (!companyStore.selectedCompanyId) {
    error.value = "Error: No se pudo identificar la empresa."
    return
  }

  if (!confirm(`⚠️ ADVERTENCIA: ¿Está seguro de revertir el cierre del período?
Se creará una nueva póliza de reversión (REV-Año) que contrarrestará los movimientos del cierre original.
El período quedará abierto para nuevas modificaciones.`)) {
    return
  }

  cargando.value = true
  error.value = ''
  exito.value = ''

  try {
    const params = {
      empresa_id: companyStore.selectedCompanyId,  // ✅ Usar empresa del contexto global
      periodo_id: periodoId
    }
    if (authStore.isSuperAdmin && selectedTenantId.value) {
      params.tenant_id = selectedTenantId.value
    }
    const resp = await api.post('/cierre/revertir-cierre', null, { params })
    exito.value = `✅ ${resp.data.mensaje}\n` +
      `📝 Póliza de reversión: ${resp.data.poliza_reversion}\n` +
      `🔄 Se contrarrestaron ${resp.data.total_lineas_revertidas} líneas de las pólizas: ${resp.data.partidas_contrarrestadas.join(', ')}`
    await cargarPeriodos()
  } catch (err) {
    error.value = formatFastApiError(err)
  } finally {
    cargando.value = false
  }
}

// ✅ Watch: Recargar períodos cuando cambie la empresa seleccionada
watch(() => companyStore.selectedCompanyId, async (newId) => {
  if (newId) {
    await cargarPeriodos()
  } else {
    periodos.value = []
  }
})

onMounted(async () => {
  await fetchTenants()
  if (authStore.isSuperAdmin && tenants.value.length > 0) {
    selectedTenantId.value = tenants.value[0].id
  }
  // ✅ Cargar períodos si ya hay empresa seleccionada
  if (companyStore.selectedCompanyId) {
    await cargarPeriodos()
  }
})
</script>