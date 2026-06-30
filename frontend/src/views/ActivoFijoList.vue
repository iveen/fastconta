<!-- src/views/ActivoFijoList.vue -->
<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-7xl mx-auto space-y-6">
      <h1 class="text-2xl font-bold text-gray-800">Activos Fijos</h1>

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
        <p class="text-lg font-semibold">Selecciona una empresa desde la barra superior para gestionar los activos fijos</p>
      </div>

      <!-- ✅ CONTENIDO PRINCIPAL (solo si hay empresa seleccionada) -->
      <div v-else>
        <!-- Barra de acciones -->
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-4">
          <div class="text-sm text-gray-600 flex items-center gap-2">
            <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            <span>Empresa:</span>
            <span class="font-semibold text-gray-800">{{ companyStore.currentCompany?.nombre || 'Sin seleccionar' }}</span>
          </div>
          <div class="flex gap-3">
            <button 
              @click="abrirModalDepreciacion"
              class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition flex items-center gap-2 text-sm shadow-sm"
            >
              <span>️</span> Procesar Depreciación Mensual
            </button>
            <button 
              @click="irACrear"
              class="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition flex items-center gap-2 text-sm shadow-sm"
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
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Código</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Descripción</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Categoría</th>
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
      :empresa-id="companyStore.selectedCompanyId"
      :nombre-empresa="companyStore.currentCompany?.nombre || ''"
      @close="modalDepreciacionAbierto = false"
      @success="activosStore.fetchActivos(companyStore.selectedCompanyId)"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useCompanyStore } from '@/stores/company'  // ✅ NUEVO
import { useActivosFijosStore } from '@/stores/activosFijos'
import api from '@/services/api'
import ProcesarDepreciacionModal from '../components/ActivosFijos/ProcesarDepreciacionModal.vue'
import { toast } from 'vue3-toastify'

const router = useRouter()
const authStore = useAuthStore()
const companyStore = useCompanyStore()  // ✅ NUEVO
const activosStore = useActivosFijosStore()
const modalDepreciacionAbierto = ref(false)

const tenants = ref([])
const selectedTenantId = ref('')

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
  activosStore.activos = []
}

// ✅ Watch: Recargar activos cuando cambie la empresa seleccionada
watch(() => companyStore.selectedCompanyId, async (newId) => {
  if (newId) {
    await activosStore.fetchActivos(newId)
  } else {
    activosStore.activos = []
  }
})

onMounted(async () => {
  await activosStore.fetchCategorias()
  await fetchTenants()
  if (authStore.isSuperAdmin && tenants.value.length > 0) {
    selectedTenantId.value = tenants.value[0].id
  }
  // ✅ Cargar activos si ya hay empresa seleccionada
  if (companyStore.selectedCompanyId) {
    await activosStore.fetchActivos(companyStore.selectedCompanyId)
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
  if (!companyStore.selectedCompanyId) {
    toast.warning("Por favor, seleccione una empresa primero.")
    return
  }
  router.push({ 
    name: 'ActivosFijosCrear', 
    query: { empresa_id: companyStore.selectedCompanyId } 
  })
}

const editarActivo = (id) => router.push({ 
  name: 'ActivosFijosEditar', 
  params: { id }, 
  query: { empresa_id: companyStore.selectedCompanyId } 
})

const verProyeccion = (id) => router.push({ 
  name: 'ActivosFijosProyeccion', 
  params: { id }, 
  query: { empresa_id: companyStore.selectedCompanyId } 
})

const abrirModalDepreciacion = () => {
  if (!companyStore.selectedCompanyId) {
    toast.warning("Seleccione una empresa primero.")
    return
  }
  modalDepreciacionAbierto.value = true
}
</script>