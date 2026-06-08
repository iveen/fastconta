<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-7xl mx-auto space-y-6">
      <h1 class="text-2xl font-bold text-gray-800">Activos Fijos</h1>

      <!-- 🔹 1. SELECTOR DE TENANT (Solo Superadmin) -->
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

      <!-- 🔹 2. SELECTOR DE EMPRESA (Superadmin y Tenant_*, pero NO para Cliente) -->
      <div v-if="!esCliente" class="bg-white shadow-md rounded-lg p-4">
        <label class="block text-gray-700 text-sm font-bold mb-2">Seleccionar Empresa</label>
        <select
          v-model="empresaSeleccionadaId"
          class="w-full md:w-1/3 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">-- Seleccione una empresa --</option>
          <option v-for="emp in empresas" :key="emp.id" :value="emp.id">
            {{ emp.nombre }} ({{ emp.nit }})
          </option>
        </select>
      </div>

      <!-- Estado vacío: Esperando selección (Solo para roles que deben seleccionar) -->
      <div v-if="!empresaSeleccionadaId && !esCliente" class="bg-white shadow-md rounded-lg p-8 text-center text-gray-500">
        Seleccione una empresa para ver sus activos fijos.
      </div>

      <!-- 🔹 3. CONTENIDO PRINCIPAL (Visible si hay empresa seleccionada o si es cliente) -->
      <div v-if="empresaSeleccionadaId || esCliente">
        
        <!-- Barra de acciones -->
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-4">
          <div class="text-sm text-gray-600">
            Empresa actual: <span class="font-semibold text-gray-800">{{ nombreEmpresaActual }}</span>
          </div>
          <div class="flex gap-3">
            <button 
              @click="abrirModalDepreciacion"
              class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition flex items-center gap-2 text-sm shadow-sm"
            >
              <span>⚙️</span> Procesar Depreciacion Mensual
            </button>
            <button 
                @click="irACrear"
                :disabled="!empresaSeleccionadaId"
                class="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition flex items-center gap-2 text-sm shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
                <span>+</span> Nuevo Activo
            </button>
          </div>
        </div>

        <!-- Tabla de Activos -->
        <div v-if="activosStore.loading" class="text-center py-8 text-gray-500 bg-white rounded-lg shadow">
          Cargando activos...
        </div>
        
        <div v-else-if="activosStore.activos.length === 0" class="bg-white shadow-md rounded-lg p-8 text-center text-gray-500">
          No hay activos fijos registrados para esta empresa.
        </div>
        
        <div v-else class="bg-white shadow-md rounded-lg overflow-hidden">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Codigo</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Descripcion</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Categoria</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Valor Costo</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Valor en Libros</th>
                <th class="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Estado</th>
                <th class="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Acciones</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="activo in activosStore.activos" :key="activo.id" class="hover:bg-gray-50">
                <td class="px-4 py-3 whitespace-nowrap text-sm font-mono text-gray-900">{{ activo.codigo_interno }}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">{{ activo.descripcion }}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">{{ activo.categoria?.nombre }}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900 text-right">Q {{ formatMoney(activo.valor_costo) }}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm font-semibold text-gray-900 text-right">Q {{ formatMoney(activo.valor_en_libros || calcularValorLibros(activo)) }}</td>
                <td class="px-4 py-3 whitespace-nowrap text-center">
                  <span :class="getEstadoBadgeClass(activo.estado)" class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full">
                    {{ activo.estado }}
                  </span>
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-center text-sm font-medium">
                  <button @click="verProyeccion(activo.id)" class="text-indigo-600 hover:text-indigo-900 mr-3">Ver Tabla</button>
                  <button @click="editarActivo(activo.id)" class="text-gray-600 hover:text-gray-900">Editar</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
    <!-- Modal de Procesamiento de Depreciación Mensual -->
    <ProcesarDepreciacionModal
      :is-open="modalDepreciacionAbierto"
      :empresa-id="empresaSeleccionadaId"
      :nombre-empresa="nombreEmpresaActual"
      @close="modalDepreciacionAbierto = false"
      @success="activosStore.fetchActivos(empresaSeleccionadaId)"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useActivosFijosStore } from '@/stores/activosFijos'
import api from '@/services/api'
import ProcesarDepreciacionModal from '../components/ActivosFijos/ProcesarDepreciacionModal.vue'
import { toast } from 'vue3-toastify'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const activosStore = useActivosFijosStore()
const modalDepreciacionAbierto = ref(false)

const tenants = ref([])
const selectedTenantId = ref('')
const empresas = ref([])
const empresaSeleccionadaId = ref('')

// 🔹 Detectar si el usuario es cliente (Ajusta esta condición a tu lógica real de authStore)
const esCliente = computed(() => {
  return authStore.esCliente || authStore.user?.rol === 'cliente' || authStore.user?.role_id === 'ID_DEL_ROL_CLIENTE'
})

const nombreEmpresaActual = computed(() => {
  const emp = empresas.value.find(e => e.id === empresaSeleccionadaId.value)
  return emp ? emp.nombre : 'Sin seleccionar'
})

const fetchTenants = async () => {
  if (!authStore.isSuperAdmin) return
  try {
    const res = await api.get('/tenants/')
    tenants.value = res.data.filter(t => !['sistema', 'system', 'public'].includes(t.schema_name))
    if (tenants.value.length > 0 && !selectedTenantId.value) {
      selectedTenantId.value = tenants.value[0].id
    }
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
    // Si es superadmin, filtra por tenant_id. Si es tenant_*, trae las asignadas a su tenant.
    const params = authStore.isSuperAdmin ? { tenant_id: selectedTenantId.value } : {}
    const response = await api.get('/empresas/', { params })
    empresas.value = response.data
    
    // 🔹 PATRÓN: Si es cliente, o si solo hay 1 empresa, se auto-selecciona
    if (esCliente.value || empresas.value.length === 1) {
      empresaSeleccionadaId.value = empresas.value[0].id
    }
  } catch (err) {
    console.error('Error al cargar empresas:', err)
  }
}

const handleTenantChange = () => {
  empresaSeleccionadaId.value = ''
  activosStore.activos = []
  cargarEmpresas()
}

// Observar cambios en la empresa seleccionada para cargar sus activos
watch(empresaSeleccionadaId, async (nuevoId) => {
  if (nuevoId) {
    await activosStore.fetchActivos(nuevoId)
  } else {
    activosStore.activos = []
  }
})

onMounted(async () => {
  await activosStore.fetchCategorias()
  await fetchTenants()
  await cargarEmpresas()
  if (route.query.empresa_id) {
    empresaSeleccionadaId.value = route.query.empresa_id
  }
})

const formatMoney = (value) => {
  return Number(value).toLocaleString('es-GT', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const calcularValorLibros = (activo) => {
  return (Number(activo.valor_costo) - Number(activo.valor_residual)).toFixed(2)
}

const getEstadoBadgeClass = (estado) => {
  const map = {
    'activo': 'bg-green-100 text-green-800',
    'totalmente_depreciado': 'bg-gray-100 text-gray-800',
    'dado_baja': 'bg-red-100 text-red-800',
    'vendido': 'bg-blue-100 text-blue-800'
  }
  return map[estado] || 'bg-gray-100 text-gray-800'
}

const irACrear = () => {
  if (!empresaSeleccionadaId.value) {
    toast.warning("Por favor, seleccione una empresa primero.")
    return
  }
  router.push({ 
    name: 'ActivosFijosCrear', 
    query: { empresa_id: empresaSeleccionadaId.value } 
  })
}

const editarActivo = (id) => router.push({ name: 'ActivosFijosEditar', params: { id }, query: { empresa_id: empresaSeleccionadaId.value } })
const verProyeccion = (id) => router.push({ name: 'ActivosFijosProyeccion', params: { id }, query: { empresa_id: empresaSeleccionadaId.value } })

const abrirModalDepreciacion = () => {
  if (!empresaSeleccionadaId.value) {
    toast.warning("Seleccione una empresa primero.")
    return
  }
  modalDepreciacionAbierto.value = true
}
</script>