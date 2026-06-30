<!-- src/views/Partidas.vue -->
<template>
<div class="min-h-screen bg-gray-50 p-6">
  <div class="max-w-7xl mx-auto space-y-6">
    <!-- Encabezado -->
    <div class="flex justify-between items-center">
      <h2 class="text-2xl font-bold text-gray-800">Partidas Contables</h2>
      <button
        @click="mostrarFormulario = !mostrarFormulario"
        :disabled="!companyStore.selectedCompanyId"
        class="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600 transition disabled:bg-gray-400 disabled:cursor-not-allowed"
        :title="!companyStore.selectedCompanyId ? 'Selecciona una empresa primero' : ''"
      >
        {{ mostrarFormulario ? 'Cancelar' : 'Nueva Partida' }}
      </button>
    </div>

    <!-- Mensajes de Error y Éxito -->
    <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">{{ error }}</div>
    <div v-if="successMsg" class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4 flex justify-between items-center">
      <span>{{ successMsg }}</span>
      <button @click="successMsg = ''" class="text-sm underline hover:no-underline">Cerrar</button>
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

    <!-- ✅ MENSAJE SI NO HAY EMPRESA SELECCIONADA -->
    <div v-if="!companyStore.selectedCompanyId" class="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-12 rounded-lg text-center">
      <svg class="w-12 h-12 mx-auto mb-3 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
      <p class="text-lg font-semibold">Selecciona una empresa desde la barra superior para cargar las partidas contables</p>
    </div>

    <!-- Formulario de creación / edición -->
    <div v-if="mostrarFormulario && companyStore.selectedCompanyId" class="bg-white shadow-md rounded-lg p-6 mb-6 border-l-4 border-blue-500">
      <h3 class="text-lg font-semibold mb-4">
        {{ isEditing ? '✏️ Editar Partida' : '➕ Nueva Partida' }}
        <span v-if="isEditing" class="text-sm font-normal text-gray-500 ml-2">(Póliza: {{ nuevaPartida.numero_poliza }})</span>
      </h3>
      <form @submit.prevent="crearPartida">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label class="block text-gray-700 text-sm font-bold mb-2">Fecha</label>
            <DateInput
            v-model="nuevaPartida.fecha"
            placeholder="dd/mm/yyyy"
          />
          </div>
          <div>
            <label class="block text-gray-700 text-sm font-bold mb-2">Número Póliza</label>
            <input v-model="nuevaPartida.numero_poliza" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-md" placeholder="Auto-generado si se deja vacío" />
          </div>
          <div class="bg-gray-100 rounded px-3 py-2 flex items-center">
            <span class="text-xs text-gray-500 uppercase">Empresa activa</span>
            <span class="ml-2 font-bold text-gray-800">{{ companyStore.currentCompany?.nombre || 'Desconocida' }}</span>
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
        <div class="flex items-center">
          <button type="submit" :disabled="cargando || !companyStore.selectedCompanyId" class="bg-green-500 text-white px-6 py-2 rounded-md hover:bg-green-600 transition disabled:opacity-50 font-medium">
            {{ cargando ? (isEditing ? 'Guardando...' : 'Creando...') : (isEditing ? 'Guardar Cambios' : 'Crear Partida') }}
          </button>
          <button v-if="isEditing" type="button" @click="cancelarEdicion" class="ml-3 text-gray-600 hover:text-gray-800 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50">
            Cancelar
          </button>
        </div>
      </form>
    </div>

    <!-- TABLA DE PARTIDAS -->
    <div v-else-if="companyStore.selectedCompanyId">
      <div v-if="cargandoLista" class="text-center py-8 text-gray-500">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-2"></div>
        <p>Cargando partidas...</p>
      </div>
      <div v-else-if="partidas.length === 0" class="bg-white shadow-md rounded-lg p-8 text-center text-gray-500">
        No se encontraron partidas para esta empresa.
      </div>
      <div v-else class="bg-white shadow-md rounded-lg overflow-hidden">
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th @click="toggleOrder('numero_poliza')" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer select-none hover:bg-gray-100 whitespace-nowrap">
                  Póliza {{ sortIcon('numero_poliza') }}
                </th>
                <th @click="toggleOrder('fecha')" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer select-none hover:bg-gray-100 whitespace-nowrap">
                  Fecha {{ sortIcon('fecha') }}
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Descripción
                </th>
                <th @click="toggleOrder('debe')" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer select-none hover:bg-gray-100 whitespace-nowrap">
                  Debe {{ sortIcon('debe') }}
                </th>
                <th @click="toggleOrder('haber')" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer select-none hover:bg-gray-100 whitespace-nowrap">
                  Haber {{ sortIcon('haber') }}
                </th>
                <th v-if="!isEditing" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="p in partidasFiltradas" :key="String(p.id)" class="hover:bg-gray-50 transition-colors" :class="{'bg-red-50': !p.is_active}">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-mono">
                  <router-link :to="`/dashboard/partidas/${p.id}`" class="text-blue-600 hover:text-blue-900 font-semibold">
                    {{ p.numero_poliza || 'S/N' }}
                  </router-link>
                  <span v-if="!p.is_active" class="ml-2 text-xs text-red-500 font-bold">(Eliminada)</span>
                  <span v-if="p.fue_revertida" class="ml-2 text-xs text-orange-500 font-bold">(Revertida)</span>
                  <span v-if="p.tipo_origen === 'cierre'" class="ml-2 text-xs text-purple-500 font-bold">(Cierre)</span>
                  <span v-if="p.tipo_origen === 'reversion_cierre'" class="ml-2 text-xs text-purple-500 font-bold">(Rev. Cierre)</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                  {{ p.fecha }}
                </td>
                <td class="px-6 py-4 text-sm text-gray-700 max-w-md">
                  <div class="line-clamp-2" :title="p.descripcion">
                    {{ p.descripcion }}
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-right font-mono">
                  <span class="text-blue-600 font-semibold">
                    {{ formatearMonto(calcularTotal(p, 'debe')) }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-right font-mono">
                  <span class="text-red-600 font-semibold">
                    {{ formatearMonto(calcularTotal(p, 'haber')) }}
                  </span>
                </td>
                <td v-if="p.is_active && !['cierre', 'reversion_cierre'].includes(p.tipo_origen) && !isEditing" class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                  <button
                    v-if="p.is_active"
                    @click="prepararEdicion(p)"
                    class="text-indigo-600 hover:text-indigo-900 p-1 rounded hover:bg-indigo-50"
                    title="Editar"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    v-if="p.is_active"
                    @click="revertirPartida(p)"
                    class="text-yellow-600 hover:text-yellow-900 p-1 rounded hover:bg-yellow-50"
                    title="Revertir"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                  </button>
                  <button
                    v-if="p.is_active"
                    @click="eliminarPartida(p.id)"
                    class="text-red-600 hover:text-red-900 p-1 rounded hover:bg-red-50"
                    title="Eliminar"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <!-- Footer con totales -->
        <div class="bg-gray-50 px-6 py-4 border-t border-gray-200">
          <div class="flex justify-end space-x-8 text-sm">
            <div class="text-gray-600">
              <span class="font-medium">Total Debe: </span>
              <span class="text-blue-600 font-mono font-semibold">
                {{ formatearMonto(partidasFiltradas.reduce((sum, p) => sum + calcularTotal(p, 'debe'), 0)) }}
              </span>
            </div>
            <div class="text-gray-600">
              <span class="font-medium">Total Haber: </span>
              <span class="text-red-600 font-mono font-semibold">
                {{ formatearMonto(partidasFiltradas.reduce((sum, p) => sum + calcularTotal(p, 'haber'), 0)) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useCompanyStore } from '@/stores/company'  // ✅ NUEVO
import api from '@/services/api'
import { formatFastApiError } from '@/utils/errorHandler'
import DateInput from '@/components/DateInput.vue'

const authStore = useAuthStore()
const companyStore = useCompanyStore()  // ✅ NUEVO

// Variables de estado
const tenants = ref([])
const selectedTenantId = ref('')
const partidas = ref([])
const cuentasDisponibles = ref([])
const mostrarFormulario = ref(false)
const cargando = ref(false)
const cargandoLista = ref(false)
const error = ref('')
const successMsg = ref('')
const busqueda = ref('')
const orderField = ref('fecha')
const orderDirection = ref('desc')

// Estado para edición
const isEditing = ref(false)
const partidaOriginalId = ref(null)
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

// ✅ CORRECCIÓN: Cargar cuentas usando companyStore y filtrar duplicados con Map
const cargarCuentas = async () => {
  if (!companyStore.selectedCompanyId) {
    cuentasDisponibles.value = []
    return
  }

  try {
    const params = {}
    if (authStore.isSuperAdmin && selectedTenantId.value) {
      params.tenant_id = selectedTenantId.value
    }
    
    // ✅ El interceptor de Axios ya inyecta X-Company-Id automáticamente
    const resp = await api.get('/plan-cuentas/', { params })
    
    // ✅ DEBUG: Ver qué está llegando del backend
    console.log('📊 Cuentas recibidas del backend:', resp.data.length)
    console.log('📊 Primeras 3 cuentas:', resp.data.slice(0, 3))
    
    // ✅ ELIMINAR DUPLICADOS usando Map (más eficiente y confiable)
    const mapaCuentas = new Map()
    resp.data.forEach(cuenta => {
      // Usar el ID como clave única
      if (!mapaCuentas.has(cuenta.id)) {
        mapaCuentas.set(cuenta.id, cuenta)
      } else {
        console.warn('⚠️ Cuenta duplicada detectada:', cuenta.id, cuenta.codigo)
      }
    })
    
    cuentasDisponibles.value = Array.from(mapaCuentas.values())
    
    console.log(`✅ Cuentas únicas después de filtrar: ${cuentasDisponibles.value.length}`)
  } catch (err) {
    console.error('Error cargando cuentas:', err)
  }
}

// ✅ CORRECCIÓN: Cargar partidas usando companyStore
const cargarPartidas = async () => {
  if (!companyStore.selectedCompanyId) {
    partidas.value = []
    return
  }

  cargandoLista.value = true
  error.value = ''

  try {
    const params = {}
    if (authStore.isSuperAdmin && selectedTenantId.value) {
      params.tenant_id = selectedTenantId.value
    }
    
    // ✅ El interceptor de Axios ya inyecta X-Company-Id automáticamente
    const r = await api.get('/partidas/', { params })
    partidas.value = r.data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al cargar partidas'
  } finally {
    cargandoLista.value = false
  }
}

// ✅ CORRECCIÓN: Solo para superadmin cambiar de tenant
const handleTenantChange = () => {
  cargarPartidas()
  cargarCuentas()
}

// ✅ Watch: Recargar datos cuando cambia la empresa seleccionada (contexto global)
watch(() => companyStore.selectedCompanyId, async (newId) => {
  if (newId) {
    await cargarCuentas()
    await cargarPartidas()
  } else {
    partidas.value = []
    cuentasDisponibles.value = []
    nuevaPartida.value.detalles = []
  }
})

// Funciones auxiliares
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

// CRUD: Agregar/Eliminar detalles
function agregarDetalle() {
  if (!companyStore.selectedCompanyId) return
  nuevaPartida.value.detalles.push({ cuenta_id: '', tipo_movimiento: 'debe', monto: null })
}

function eliminarDetalle(i) {
  nuevaPartida.value.detalles.splice(i, 1)
}

// 🔄 FUNCIÓN: Preparar formulario para editar
function prepararEdicion(partida) {
  isEditing.value = true
  partidaOriginalId.value = partida.id
  nuevaPartida.value = {
    fecha: partida.fecha,
    descripcion: partida.descripcion,
    numero_poliza: partida.numero_poliza,
    detalles: partida.detalles.map(d => ({
      cuenta_id: String(d.cuenta_id),
      tipo_movimiento: d.tipo_movimiento,
      monto: parseFloat(d.monto)
    }))
  }
  mostrarFormulario.value = true
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function cancelarEdicion() {
  isEditing.value = false
  partidaOriginalId.value = null
  nuevaPartida.value = { fecha: '', descripcion: '', numero_poliza: '', detalles: [] }
  mostrarFormulario.value = false
}

// ✏️ FUNCIÓN: Guardar (Create o Update)
const crearPartida = async () => {
  if (!companyStore.selectedCompanyId) {
    error.value = 'Debes seleccionar una empresa antes de guardar la partida'
    return
  }

  cargando.value = true
  error.value = ''
  successMsg.value = ''

  try {
    const payload = {
      fecha: nuevaPartida.value.fecha,
      descripcion: nuevaPartida.value.descripcion,
      numero_poliza: nuevaPartida.value.numero_poliza || null,
      detalles: nuevaPartida.value.detalles.map(d => ({
        cuenta_id: d.cuenta_id,
        tipo_movimiento: d.tipo_movimiento,
        monto: d.monto
      }))
    }

    if (isEditing.value) {
      await api.put(`/partidas/${partidaOriginalId.value}`, payload)
      successMsg.value = '✅ Partida actualizada exitosamente.'
    } else {
      await api.post('/partidas/', payload)
      successMsg.value = '✅ Partida creada y cuadrada exitosamente.'
    }

    cancelarEdicion()
    await cargarPartidas()
    setTimeout(() => { successMsg.value = '' }, 3000)
  } catch (err) {
    error.value = formatFastApiError(err)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } finally {
    cargando.value = false
  }
}

// 🗑️ FUNCIÓN: Eliminar (Soft Delete)
const eliminarPartida = async (id) => {
  if (!confirm('⚠️ ¿Estás seguro de eliminar esta partida? Esta acción no se puede deshacer (se marcará como inactiva).')) return

  try {
    await api.delete(`/partidas/${id}`)
    successMsg.value = '✅ Partida eliminada correctamente.'
    await cargarPartidas()
    setTimeout(() => { successMsg.value = '' }, 3000)
  } catch (err) {
    error.value = formatFastApiError(err)
  }
}

// 🔄 FUNCIÓN: Revertir Partida
const revertirPartida = async (partida) => {
  const confirmacion = confirm(`🔄 ¿Deseas generar una póliza de reversión para la Póliza ${partida.numero_poliza}?
Se creará una nueva partida con fecha de hoy invirtiendo los montos.`)

  if (!confirmacion) return

  try {
    const payload = { fecha_reversion: new Date().toISOString().split('T')[0] }
    const res = await api.post(`/partidas/${partida.id}/revertir`, payload)
    successMsg.value = `✅ Reversión exitosa. Nueva Póliza: ${res.data.numero_poliza}`
    await cargarPartidas()
    setTimeout(() => { successMsg.value = '' }, 4000)
  } catch (err) {
    error.value = formatFastApiError(err)
  }
}

onMounted(async () => {
  await fetchTenants()
  if (authStore.isSuperAdmin && tenants.value.length > 0) {
    selectedTenantId.value = tenants.value[0].id
  }
  // ✅ Ya no llamamos a cargarEmpresas(), solo cargamos datos si hay empresa seleccionada
  if (companyStore.selectedCompanyId) {
    await cargarCuentas()
    await cargarPartidas()
  }
})
</script>