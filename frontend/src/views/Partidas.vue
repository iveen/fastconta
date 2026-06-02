<!-- src/views/Partidas.vue -->
<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-6xl mx-auto space-y-6">
      <div class="flex justify-between items-center">
        <h2 class="text-2xl font-bold text-gray-800">Partidas Contables</h2>
        <button
          @click="mostrarFormulario = !mostrarFormulario"
          :disabled="!empresaFiltroId"
          class="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600 transition disabled:bg-gray-400 disabled:cursor-not-allowed"
          :title="!empresaFiltroId ? 'Selecciona una empresa primero' : ''"
        >
          {{ mostrarFormulario ? 'Cancelar' : 'Nueva Partida' }}
        </button>
      </div>

      <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">{{ error }}</div>

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

      <!-- Filtros y búsqueda -->
      <div class="bg-white shadow-md rounded-lg p-4 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label class="block text-gray-700 text-sm font-bold mb-2">Filtrar por Empresa</label>
          <select
            v-model="empresaFiltroId"
            @change="onEmpresaChange"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">-- Seleccione una empresa --</option>
            <option 
              v-for="emp in empresas" 
              :key="String(emp.id)" 
              :value="String(emp.id)"
            >
              {{ emp.nombre }}
            </option>
          </select>
        </div>
        <div class="md:col-span-2 flex items-end">
          <div class="w-full">
            <label class="block text-gray-700 text-sm font-bold mb-2">Buscar</label>
            <input
              v-model="busqueda"
              type="text"
              placeholder="Buscar por póliza, descripción o fecha..."
              :disabled="!empresaFiltroId"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
            />
          </div>
        </div>
      </div>

      <!-- MENSAJE SI NO HAY EMPRESA SELECCIONADA -->
      <div v-if="!empresaFiltroId" class="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-12 rounded-lg text-center">
        <svg class="w-12 h-12 mx-auto mb-3 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
        <p class="text-lg font-semibold">Selecciona una empresa para cargar las partidas contables</p>
      </div>

      <!-- Formulario de creación -->
      <div v-if="mostrarFormulario && empresaFiltroId" class="bg-white shadow-md rounded-lg p-6 mb-6 border-l-4 border-blue-500">
        <h3 class="text-lg font-semibold mb-4">Nueva Partida</h3>
        <form @submit.prevent="crearPartida">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label class="block text-gray-700 text-sm font-bold mb-2">Fecha</label>
              <input v-model="nuevaPartida.fecha" type="date" class="w-full px-3 py-2 border border-gray-300 rounded-md" required />
            </div>
            <div>
              <label class="block text-gray-700 text-sm font-bold mb-2">Número Póliza (opcional)</label>
              <input v-model="nuevaPartida.numero_poliza" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-md" placeholder="Auto-generado" />
            </div>
            <div class="bg-gray-100 rounded px-3 py-2 flex items-center">
              <span class="text-xs text-gray-500 uppercase">Empresa activa</span>
              <span class="ml-2 font-bold text-gray-800">{{ obtenerNombreEmpresa(empresaFiltroId) }}</span>
            </div>
          </div>
          <div class="mb-4">
            <label class="block text-gray-700 text-sm font-bold mb-2">Descripción</label>
            <textarea v-model="nuevaPartida.descripcion" class="w-full px-3 py-2 border border-gray-300 rounded-md" rows="2" required></textarea>
          </div>
          <div class="mb-4">
            <div class="flex justify-between items-center mb-2">
              <h4 class="font-semibold text-gray-700">Detalles</h4>
              <button type="button" @click="agregarDetalle" class="text-blue-500 hover:text-blue-700 text-sm font-medium">+ Agregar línea</button>
            </div>
            <div v-for="(detalle, index) in nuevaPartida.detalles" :key="index" class="flex gap-2 mb-2 items-start">
              <select 
                v-model="detalle.cuenta_id" 
                class="w-full px-2 py-2 border border-gray-300 rounded-md text-sm" 
                required
                :disabled="!empresaFiltroId"
              >
                <option value="">Seleccionar cuenta...</option>
                <option v-for="c in cuentasDisponibles" :key="String(c.id)" :value="String(c.id)">
                  {{ c.codigo }} - {{ c.nombre }}
                </option>
              </select>
              <select v-model="detalle.tipo_movimiento" class="w-24 px-2 py-2 border border-gray-300 rounded-md text-sm" required>
                <option value="debe">Debe</option>
                <option value="haber">Haber</option>
              </select>
              <input v-model.number="detalle.monto" type="number" step="0.01" min="0.01" class="w-32 px-2 py-2 border border-gray-300 rounded-md text-sm" placeholder="Monto" required />
              <button type="button" @click="eliminarDetalle(index)" class="text-red-500 hover:text-red-700 text-sm mt-2 px-2">✕</button>
            </div>
          </div>
          <button type="submit" :disabled="cargando || !empresaFiltroId" class="bg-green-500 text-white px-6 py-2 rounded-md hover:bg-green-600 transition disabled:opacity-50 font-medium">
            {{ cargando ? 'Creando...' : 'Crear Partida' }}
          </button>
        </form>
      </div>

      <!-- TABLA DE PARTIDAS -->
      <div v-else-if="empresaFiltroId">
        <div v-if="cargandoLista" class="text-center py-8 text-gray-500">
          <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-2"></div>
          <p>Cargando partidas...</p>
        </div>
        <div v-else-if="partidas.length === 0" class="bg-white shadow-md rounded-lg p-8 text-center text-gray-500">
          No se encontraron partidas para esta empresa.
        </div>
        <div v-else class="bg-white shadow-md rounded-lg overflow-hidden">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th @click="toggleOrder('numero_poliza')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer select-none hover:bg-gray-100">
                  Póliza {{ sortIcon('numero_poliza') }}
                </th>
                <th @click="toggleOrder('fecha')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer select-none hover:bg-gray-100">
                  Fecha {{ sortIcon('fecha') }}
                </th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Descripción</th>
                <th @click="toggleOrder('debe')" class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase cursor-pointer select-none hover:bg-gray-100">
                  Debe {{ sortIcon('debe') }}
                </th>
                <th @click="toggleOrder('haber')" class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase cursor-pointer select-none hover:bg-gray-100">
                  Haber {{ sortIcon('haber') }}
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="p in partidasFiltradas" :key="String(p.id)" class="hover:bg-gray-50">
                <td class="px-4 py-3 whitespace-nowrap text-sm font-mono text-blue-600 hover:text-blue-800">
                  <router-link :to="`/dashboard/partidas/${p.id}`">
                    {{ p.numero_poliza || 'S/N' }}
                  </router-link>
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">{{ p.fecha }}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">{{ p.descripcion }}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-right text-blue-600 tabular-nums">
                  {{ formatearMonto(calcularTotal(p, 'debe')) }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-right text-red-600 tabular-nums">
                  {{ formatearMonto(calcularTotal(p, 'haber')) }}
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
import { ref, onMounted, computed, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

const authStore = useAuthStore()

const tenants = ref([])
const selectedTenantId = ref('')
const empresas = ref([])
const empresaFiltroId = ref('')
const partidas = ref([])
const cuentasDisponibles = ref([])
const mostrarFormulario = ref(false)
const cargando = ref(false)
const cargandoLista = ref(false)
const error = ref('')
const busqueda = ref('')
const orderField = ref('fecha')
const orderDirection = ref('desc')

const nuevaPartida = ref({
  fecha: '',
  descripcion: '',
  numero_poliza: '',
  detalles: []
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
    const r = await api.get('/empresas/', { params })
    empresas.value = r.data
  } catch {
    error.value = 'Error al cargar empresas'
  }
}

const handleTenantChange = () => {
  empresaFiltroId.value = ''
  partidas.value = []
  cuentasDisponibles.value = []
  cargarEmpresas()
}

watch(empresaFiltroId, async (nuevoId) => {
  if (!nuevoId) {
    partidas.value = []
    cuentasDisponibles.value = []
    nuevaPartida.value.detalles = []
    return
  }

  try {
    const params = { empresa_id: nuevoId }
    if (authStore.isSuperAdmin && selectedTenantId.value) {
      params.tenant_id = selectedTenantId.value
    }
    const resp = await api.get('/plan-cuentas/', { params })
    cuentasDisponibles.value = resp.data
  } catch (err) {
    console.error('Error cargando cuentas:', err)
  }
})

function obtenerNombreEmpresa(id) {
  const emp = empresas.value.find(e => String(e.id) === String(id))
  return emp ? emp.nombre : 'Desconocida'
}

function formatearMonto(valor) {
  const num = parseFloat(valor)
  return isNaN(num) ? '0.00' : num.toFixed(2)
}

function calcularTotal(partida, tipo) {
  if (!partida.detalles) return 0
  return partida.detalles
    .filter(d => d.tipo_movimiento === tipo)
    .reduce((acc, d) => acc + parseFloat(d.monto || 0), 0)
}

const partidasFiltradas = computed(() => {
  let resultado = partidas.value.map(p => {
    return {
      ...p,
      _totalDebe: calcularTotal(p, 'debe'),
      _totalHaber: calcularTotal(p, 'haber')
    }
  })

  if (busqueda.value.trim()) {
    const term = busqueda.value.toLowerCase()
    resultado = resultado.filter(p =>
      (p.numero_poliza && p.numero_poliza.toLowerCase().includes(term)) ||
      p.descripcion.toLowerCase().includes(term) ||
      String(p.fecha).includes(term)
    )
  }

  resultado.sort((a, b) => {
    let valA, valB
    switch (orderField.value) {
      case 'fecha':
        valA = new Date(a.fecha)
        valB = new Date(b.fecha)
        break
      case 'numero_poliza':
        valA = a.numero_poliza || ''
        valB = b.numero_poliza || ''
        return orderDirection.value === 'asc'
          ? String(valA).localeCompare(String(valB))
          : String(valB).localeCompare(String(valA))
      case 'debe':
        valA = a._totalDebe
        valB = b._totalDebe
        break
      case 'haber':
        valA = a._totalHaber
        valB = b._totalHaber
        break
      default:
        return 0
    }
    if (valA < valB) return orderDirection.value === 'asc' ? -1 : 1
    if (valA > valB) return orderDirection.value === 'asc' ? 1 : -1
    return 0
  })

  return resultado
})

function toggleOrder(field) {
  if (orderField.value === field) {
    orderDirection.value = orderDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    orderField.value = field
    orderDirection.value = 'asc'
  }
}

function sortIcon(field) {
  if (orderField.value !== field) return '↕'
  return orderDirection.value === 'asc' ? '↑' : '↓'
}

async function onEmpresaChange() {
  await cargarPartidas()
}

async function cargarPartidas() {
  if (!empresaFiltroId.value) {
    partidas.value = []
    return
  }

  cargandoLista.value = true
  error.value = ''
  try {
    const params = { empresa_id: empresaFiltroId.value }
    if (authStore.isSuperAdmin && selectedTenantId.value) {
      params.tenant_id = selectedTenantId.value
    }
    const r = await api.get('/partidas/', { params })
    partidas.value = r.data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al cargar partidas'
  } finally {
    cargandoLista.value = false
  }
}

function agregarDetalle() {
  if (!empresaFiltroId.value) return
  nuevaPartida.value.detalles.push({ cuenta_id: '', tipo_movimiento: 'debe', monto: null })
}

function eliminarDetalle(i) {
  nuevaPartida.value.detalles.splice(i, 1)
}

async function crearPartida() {
  if (!empresaFiltroId.value) {
    error.value = 'Debes seleccionar una empresa antes de crear la partida'
    return
  }

  cargando.value = true
  try {
    await api.post('/partidas/', {
      fecha: nuevaPartida.value.fecha,
      descripcion: nuevaPartida.value.descripcion,
      numero_poliza: nuevaPartida.value.numero_poliza || null,
      detalles: nuevaPartida.value.detalles.map(d => ({
        cuenta_id: d.cuenta_id,
        tipo_movimiento: d.tipo_movimiento,
        monto: d.monto
      }))
    })
    nuevaPartida.value = { fecha: '', descripcion: '', numero_poliza: '', detalles: [] }
    mostrarFormulario.value = false
    await cargarPartidas()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al crear partida'
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