<!-- src/views/inventarios/InventarioTomasList.vue -->
<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="flex items-center justify-between mb-8">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">Inventarios</h1>
          <p class="mt-1 text-sm text-gray-500">
            Gestión de tomas de inventario físico valuadas
          </p>
        </div>
        <div class="flex gap-3">
          <button
            @click="mostrarCatalogos = true"
            class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            📦 Catálogos
          </button>
          <button
            @click="abrirModalCrear = true"
            class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
          >
            + Nueva Toma
          </button>
        </div>
      </div>

      <!-- Filtros -->
      <div class="bg-white rounded-lg shadow-sm border border-gray-100 p-4 mb-6">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Empresa</label>
            <select v-model="filtros.empresa_public_id" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm">
              <option value="">Todas las empresas</option>
              <option v-for="emp in empresas" :key="emp.public_id" :value="emp.public_id">
                {{ emp.nombre }}
              </option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Estado</label>
            <select v-model="filtros.estado" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm">
              <option value="">Todos</option>
              <option value="BORRADOR">Borrador</option>
              <option value="CONFIRMADO">Confirmado</option>
              <option value="CONTABILIZADO">Contabilizado</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Tipo</label>
            <select v-model="filtros.tipo" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm">
              <option value="">Todos</option>
              <option value="FISCAL">Fiscal</option>
              <option value="INTERNO">Interno</option>
              <option value="AJUSTE">Ajuste</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Año</label>
            <input v-model.number="filtros.anio" type="number" placeholder="Ej: 2026" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" />
          </div>
        </div>
      </div>

      <!-- Lista de Tomas -->
      <div class="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
        <div v-if="cargando" class="p-12 text-center text-gray-500">
          <span class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></span>
          <p class="mt-2">Cargando tomas...</p>
        </div>

        <div v-else-if="tomas.length === 0" class="p-12 text-center">
          <Package class="w-16 h-16 mx-auto text-gray-300 mb-4" />
          <p class="text-gray-500 mb-4">No hay tomas de inventario registradas</p>
          <button @click="abrirModalCrear = true" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
            Crear primera toma
          </button>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Período</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha Corte</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Método</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Items</th>
                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Valor Total</th>
                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="toma in tomas" :key="toma.public_id" class="hover:bg-gray-50 transition-colors">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {{ toma.anio_periodo }}/{{ String(toma.mes_periodo).padStart(2, '0') }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ formatearFecha(toma.fecha_corte) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span :class="tipoBadgeClass(toma.tipo)" class="px-2 py-1 rounded text-xs font-semibold">
                    {{ toma.tipo }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ metodoLabel(toma.metodo_valuacion) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span :class="estadoBadgeClass(toma.estado)" class="px-2 py-1 rounded-full text-xs font-semibold">
                    {{ toma.estado }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                  {{ toma.total_items }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 text-right">
                  Q {{ Number(toma.valor_total).toLocaleString('es-GT', { minimumFractionDigits: 2 }) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm">
                  <button
                    @click="verDetalle(toma.public_id)"
                    class="text-blue-600 hover:text-blue-800 font-medium mr-3"
                  >
                    Ver
                  </button>
                  <button
                    v-if="toma.estado === 'BORRADOR'"
                    @click="eliminarToma(toma)"
                    class="text-red-600 hover:text-red-800 font-medium"
                  >
                    Eliminar
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Modal Crear Toma -->
    <ModalCrearToma
      v-if="abrirModalCrear"
      :empresas="empresas"
      @close="abrirModalCrear = false"
      @creado="onTomaCreada"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useCompanyStore } from '@/stores/company'
import { inventarioService } from '@/services/inventarioService'
import { toast } from 'vue3-toastify'
import { Package } from '@lucide/vue'
import ModalCrearToma from '@/components/inventarios/ModalCrearToma.vue'

const router = useRouter()
const companyStore = useCompanyStore()

const tomas = ref([])
const empresas = ref([])
const cargando = ref(false)
const abrirModalCrear = ref(false)
const mostrarCatalogos = ref(false)

const filtros = ref({
  empresa_public_id: '',
  estado: '',
  tipo: '',
  anio: new Date().getFullYear()
})

onMounted(async () => {
  await cargarEmpresas()
  await cargarTomas()
})

watch(filtros, () => {
  cargarTomas()
}, { deep: true })

async function cargarEmpresas() {
  try {
    empresas.value = companyStore.availableCompanies || []
  } catch (err) {
    console.error('Error cargando empresas:', err)
  }
}

async function cargarTomas() {
  cargando.value = true
  try {
    const params = {}
    if (filtros.value.empresa_public_id) params.empresa_public_id = filtros.value.empresa_public_id
    if (filtros.value.estado) params.estado = filtros.value.estado
    if (filtros.value.tipo) params.tipo = filtros.value.tipo
    if (filtros.value.anio) params.anio = filtros.value.anio

    tomas.value = await inventarioService.listarTomas(params)
  } catch (err) {
    console.error('Error cargando tomas:', err)
    toast.error('Error al cargar las tomas de inventario')
  } finally {
    cargando.value = false
  }
}

function verDetalle(publicId) {
  router.push({ name: 'InventarioTomaDetalle', params: { id: publicId } })
}

async function eliminarToma(toma) {
  if (!confirm(`¿Eliminar la toma ${toma.anio_periodo}/${String(toma.mes_periodo).padStart(2, '0')}? Esta acción no se puede deshacer.`)) {
    return
  }
  try {
    await inventarioService.eliminarToma(toma.public_id)
    toast.success('Toma eliminada')
    await cargarTomas()
  } catch (err) {
    toast.error(err.response?.data?.detail || 'Error al eliminar la toma')
  }
}

function onTomaCreada() {
  abrirModalCrear.value = false
  cargarTomas()
}

function formatearFecha(fecha) {
  if (!fecha) return ''
  return new Date(fecha).toLocaleDateString('es-GT', {
    day: '2-digit', month: '2-digit', year: 'numeric'
  })
}

function estadoBadgeClass(estado) {
  const map = {
    'BORRADOR': 'bg-yellow-100 text-yellow-800',
    'CONFIRMADO': 'bg-blue-100 text-blue-800',
    'CONTABILIZADO': 'bg-green-100 text-green-800'
  }
  return map[estado] || 'bg-gray-100 text-gray-800'
}

function tipoBadgeClass(tipo) {
  const map = {
    'FISCAL': 'bg-purple-100 text-purple-800',
    'INTERNO': 'bg-indigo-100 text-indigo-800',
    'AJUSTE': 'bg-orange-100 text-orange-800'
  }
  return map[tipo] || 'bg-gray-100 text-gray-800'
}

function metodoLabel(metodo) {
  const map = {
    'COSTO_PROMEDIO': 'Costo Promedio',
    'PEPS': 'PEPS (Primeras Entradas)',
    'IDENTIFICACION_ESPECIFICA': 'Identificación Específica'
  }
  return map[metodo] || metodo
}
</script>