<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="flex items-center justify-between mb-8">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">Catálogos de Inventario</h1>
          <p class="mt-1 text-sm text-gray-500">
            Gestiona bodegas y productos del catálogo de inventarios
          </p>
        </div>
        <button
          @click="router.push({ name: 'Inventarios' })"
          class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          ← Volver a Inventarios
        </button>
      </div>

      <!-- Selector de empresa -->
      <div class="bg-white rounded-lg shadow-sm border border-gray-100 p-4 mb-6">
        <label class="block text-sm font-medium text-gray-700 mb-2">Empresa</label>
        <select
          v-model="empresaSeleccionada"
          class="w-full md:w-1/3 px-3 py-2 border border-gray-300 rounded-md"
        >
          <option value="">-- Selecciona una empresa --</option>
          <option v-for="emp in empresas" :key="emp.public_id" :value="emp.public_id">
            {{ emp.nombre }} ({{ emp.nit }})
          </option>
        </select>
      </div>

      <div v-if="empresaSeleccionada" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Panel Bodegas -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-100">
          <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h3 class="text-lg font-medium text-gray-900">🏭 Bodegas</h3>
            <button
              @click="abrirModalBodega"
              class="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              + Nueva
            </button>
          </div>
          <div class="p-6">
            <div v-if="bodegas.length === 0" class="text-center text-gray-500 py-8">
              No hay bodegas registradas
            </div>
            <ul v-else class="space-y-2">
              <li
                v-for="bod in bodegas"
                :key="bod.public_id"
                class="flex justify-between items-center p-3 bg-gray-50 rounded hover:bg-gray-100"
              >
                <div>
                  <div class="font-medium text-gray-900">{{ bod.nombre }}</div>
                  <div class="text-xs text-gray-500">Código: {{ bod.codigo }}</div>
                  <div v-if="bod.ubicacion" class="text-xs text-gray-400">📍 {{ bod.ubicacion }}</div>
                </div>
                <button
                  @click="eliminarBodega(bod)"
                  class="text-red-600 hover:text-red-800 text-sm"
                >
                  Eliminar
                </button>
              </li>
            </ul>
          </div>
        </div>

        <!-- Panel Productos -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-100">
          <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h3 class="text-lg font-medium text-gray-900">📦 Productos</h3>
            <button
              @click="abrirModalProducto"
              class="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              + Nuevo
            </button>
          </div>
          <div class="p-6">
            <input
              v-model="searchProducto"
              type="text"
              placeholder="Buscar por código o descripción..."
              class="w-full px-3 py-2 border border-gray-300 rounded-md mb-4"
            />
            <div v-if="productos.length === 0" class="text-center text-gray-500 py-8">
              No hay productos registrados
            </div>
            <ul v-else class="space-y-2 max-h-96 overflow-y-auto">
              <li
                v-for="prod in productos"
                :key="prod.public_id"
                class="flex justify-between items-center p-3 bg-gray-50 rounded hover:bg-gray-100"
              >
                <div>
                  <div class="font-medium text-gray-900">{{ prod.descripcion }}</div>
                  <div class="text-xs text-gray-500">
                    Código: {{ prod.codigo || 'N/A' }} · {{ prod.unidad_medida }}
                  </div>
                </div>
                <button
                  @click="eliminarProducto(prod)"
                  class="text-red-600 hover:text-red-800 text-sm"
                >
                  Eliminar
                </button>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <div v-else class="bg-white rounded-lg shadow-sm border border-gray-100 p-12 text-center text-gray-500">
        Selecciona una empresa para gestionar sus catálogos
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useCompanyStore } from '@/stores/company'
import { inventarioService } from '@/services/inventarioService'
import { toast } from 'vue3-toastify'

const router = useRouter()
const companyStore = useCompanyStore()

const empresas = ref([])
const empresaSeleccionada = ref('')
const bodegas = ref([])
const productos = ref([])
const searchProducto = ref('')

onMounted(() => {
  empresas.value = companyStore.availableCompanies || []
})

watch(empresaSeleccionada, async (newVal) => {
  if (newVal) {
    await Promise.all([cargarBodegas(), cargarProductos()])
  } else {
    bodegas.value = []
    productos.value = []
  }
})

watch(searchProducto, () => {
  if (empresaSeleccionada.value) cargarProductos()
})

async function cargarBodegas() {
  try {
    bodegas.value = await inventarioService.listarBodegas(empresaSeleccionada.value)
  } catch (err) {
    toast.error('Error al cargar bodegas')
  }
}

async function cargarProductos() {
  try {
    productos.value = await inventarioService.listarProductos(
      empresaSeleccionada.value,
      searchProducto.value || null
    )
  } catch (err) {
    toast.error('Error al cargar productos')
  }
}

function abrirModalBodega() {
  toast.info('Función en desarrollo')
}

function abrirModalProducto() {
  toast.info('Función en desarrollo')
}

async function eliminarBodega(bod) {
  if (!confirm(`¿Eliminar bodega "${bod.nombre}"?`)) return
  try {
    await inventarioService.eliminarBodega(bod.public_id)
    toast.success('Bodega eliminada')
    await cargarBodegas()
  } catch (err) {
    toast.error(err.response?.data?.detail || 'Error al eliminar bodega')
  }
}

async function eliminarProducto(prod) {
  if (!confirm(`¿Eliminar producto "${prod.descripcion}"?`)) return
  try {
    await inventarioService.eliminarProducto(prod.public_id)
    toast.success('Producto eliminado')
    await cargarProductos()
  } catch (err) {
    toast.error(err.response?.data?.detail || 'Error al eliminar producto')
  }
}
</script>