<template>
  <div class="p-6 space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Bitácora de Logins</h1>
        <p class="text-sm text-gray-600 mt-1">Historial de intentos de autenticación del sistema</p>
      </div>
      <div class="flex items-center gap-2">
        <select v-model="statsPeriod" @change="loadStats" class="px-3 py-2 border border-gray-300 rounded-lg text-sm">
          <option :value="1">Últimas 24 horas</option>
          <option :value="7">Últimos 7 días</option>
          <option :value="30">Últimos 30 días</option>
          <option :value="90">Últimos 90 días</option>
        </select>
        <button @click="loadAll" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2">
          <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': loading }" />
          Actualizar
        </button>
      </div>
    </div>

    <!-- Tarjetas de Estadísticas -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
            <Activity class="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <p class="text-xs text-gray-500 uppercase tracking-wide">Total</p>
            <p class="text-2xl font-bold text-gray-900">{{ stats.total_logins }}</p>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
            <CheckCircle class="w-5 h-5 text-green-600" />
          </div>
          <div>
            <p class="text-xs text-gray-500 uppercase tracking-wide">Exitosos</p>
            <p class="text-2xl font-bold text-green-600">{{ stats.successful }}</p>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
            <AlertTriangle class="w-5 h-5 text-amber-600" />
          </div>
          <div>
            <p class="text-xs text-gray-500 uppercase tracking-wide">Fallidos</p>
            <p class="text-2xl font-bold text-amber-600">{{ stats.failed }}</p>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
            <Lock class="w-5 h-5 text-red-600" />
          </div>
          <div>
            <p class="text-xs text-gray-500 uppercase tracking-wide">Bloqueados</p>
            <p class="text-2xl font-bold text-red-600">{{ stats.locked }}</p>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
            <Users class="w-5 h-5 text-indigo-600" />
          </div>
          <div>
            <p class="text-xs text-gray-500 uppercase tracking-wide">Usuarios</p>
            <p class="text-2xl font-bold text-indigo-600">{{ stats.unique_users }}</p>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
            <Globe class="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <p class="text-xs text-gray-500 uppercase tracking-wide">IPs Únicas</p>
            <p class="text-2xl font-bold text-purple-600">{{ stats.unique_ips }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Panel de emails con más fallos + Filtros -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <!-- Top emails con fallos -->
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <h3 class="font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <AlertTriangle class="w-4 h-4 text-amber-600" />
          Emails con más fallos
        </h3>
        <div v-if="stats.most_failed_emails.length === 0" class="text-sm text-gray-500 py-4 text-center">
          Sin fallos en el período seleccionado
        </div>
        <ul v-else class="space-y-2">
          <li v-for="(item, i) in stats.most_failed_emails" :key="i" 
              class="flex items-center justify-between text-sm py-1 border-b border-gray-100 last:border-0">
            <span class="text-gray-700 truncate flex-1" :title="item.email">{{ item.email }}</span>
            <span class="bg-red-100 text-red-700 text-xs font-bold px-2 py-0.5 rounded-full ml-2">
              {{ item.count }}
            </span>
          </li>
        </ul>
      </div>

      <!-- Filtros -->
      <div class="lg:col-span-2 bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <h3 class="font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <Filter class="w-4 h-4 text-blue-600" />
          Filtros de búsqueda
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div>
            <label class="block text-xs text-gray-500 mb-1">Email</label>
            <input 
              v-model="filters.email" 
              type="text" 
              placeholder="usuario@..."
              class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
              @input="debouncedLoad"
            />
          </div>
          <div>
            <label class="block text-xs text-gray-500 mb-1">Estado</label>
            <select v-model="filters.status" @change="loadAudit" 
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500">
              <option value="">Todos</option>
              <option value="SUCCESS">Exitoso</option>
              <option value="FAILED_INVALID_PASSWORD">Contraseña incorrecta</option>
              <option value="FAILED_LOCKED">Cuenta bloqueada</option>
              <option value="FAILED_USER_NOT_FOUND">Usuario no encontrado</option>
              <option value="FAILED_INACTIVE">Usuario inactivo</option>
            </select>
          </div>
          <div>
            <label class="block text-xs text-gray-500 mb-1">Desde</label>
            <input v-model="filters.from_date" type="datetime-local" 
                   class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                   @change="loadAudit" />
          </div>
          <div>
            <label class="block text-xs text-gray-500 mb-1">Hasta</label>
            <input v-model="filters.to_date" type="datetime-local" 
                   class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                   @change="loadAudit" />
          </div>
        </div>
        <div class="flex gap-2 mt-3">
          <button @click="clearFilters" class="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900">
            Limpiar filtros
          </button>
          <button @click="exportCSV" class="ml-auto px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg flex items-center gap-1">
            <Download class="w-4 h-4" />
            Exportar CSV
          </button>
        </div>
      </div>
    </div>

    <!-- Tabla de resultados -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div class="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
        <p class="text-sm text-gray-600">
          Mostrando <strong>{{ audit.length }}</strong> registros
        </p>
        <select v-model="filters.limit" @change="loadAudit" class="px-2 py-1 border border-gray-300 rounded text-sm">
          <option :value="50">50 registros</option>
          <option :value="100">100 registros</option>
          <option :value="200">200 registros</option>
          <option :value="500">500 registros</option>
        </select>
      </div>

      <div v-if="loading" class="p-12 text-center">
        <RefreshCw class="w-8 h-8 text-blue-600 animate-spin mx-auto mb-2" />
        <p class="text-sm text-gray-500">Cargando bitácora...</p>
      </div>

      <div v-else-if="audit.length === 0" class="p-12 text-center">
        <Inbox class="w-12 h-12 text-gray-300 mx-auto mb-2" />
        <p class="text-sm text-gray-500">No hay registros que coincidan con los filtros</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th class="px-4 py-2 text-left font-semibold text-gray-700">Fecha / Hora</th>
              <th class="px-4 py-2 text-left font-semibold text-gray-700">Email</th>
              <th class="px-4 py-2 text-left font-semibold text-gray-700">Estado</th>
              <th class="px-4 py-2 text-left font-semibold text-gray-700">IP</th>
              <th class="px-4 py-2 text-left font-semibold text-gray-700">Motivo</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="row in audit" :key="row.id" class="hover:bg-gray-50">
              <td class="px-4 py-2 text-gray-600 whitespace-nowrap">
                {{ formatDate(row.created_at) }}
              </td>
              <td class="px-4 py-2 text-gray-900">
                <div class="flex items-center gap-2">
                  <div class="w-7 h-7 rounded-full bg-gray-200 flex items-center justify-center text-xs font-bold text-gray-600">
                    {{ getInitials(row.email_attempted) }}
                  </div>
                  <span class="font-medium">{{ row.email_attempted }}</span>
                </div>
              </td>
              <td class="px-4 py-2">
                <span :class="getStatusBadge(row.status)" class="px-2 py-1 rounded-full text-xs font-semibold whitespace-nowrap">
                  {{ getStatusLabel(row.status) }}
                </span>
              </td>
              <td class="px-4 py-2 text-gray-600 font-mono text-xs">
                {{ row.ip_address || '—' }}
              </td>
              <td class="px-4 py-2 text-gray-600 text-xs max-w-xs truncate" :title="row.failure_reason">
                {{ row.failure_reason || '—' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '@/services/api'
import { 
  Activity, CheckCircle, AlertTriangle, Lock, Users, Globe, 
  RefreshCw, Filter, Download, Inbox 
} from '@lucide/vue'
import { toast } from 'vue3-toastify'

const loading = ref(false)
const statsPeriod = ref(7)
const stats = ref({
  total_logins: 0, successful: 0, failed: 0, locked: 0,
  unique_users: 0, unique_ips: 0, most_failed_emails: [], hourly_distribution: []
})
const audit = ref([])

const filters = reactive({
  email: '',
  status: '',
  from_date: '',
  to_date: '',
  limit: 100
})

let debounceTimer = null
function debouncedLoad() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => loadAudit(), 400)
}

async function loadStats() {
  try {
    const res = await api.get(`/auth/login-audit/stats?days=${statsPeriod.value}`)
    stats.value = res.data
  } catch (err) {
    console.error('Error cargando stats:', err)
    toast.error('Error cargando estadísticas')
  }
}

async function loadAudit() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (filters.email) params.append('email', filters.email)
    if (filters.status) params.append('status', filters.status)
    if (filters.from_date) params.append('from_date', new Date(filters.from_date).toISOString())
    if (filters.to_date) params.append('to_date', new Date(filters.to_date).toISOString())
    params.append('limit', filters.limit)
    
    const res = await api.get(`/auth/login-audit?${params.toString()}`)
    audit.value = res.data
  } catch (err) {
    console.error('Error cargando bitácora:', err)
    toast.error('Error cargando bitácora')
  } finally {
    loading.value = false
  }
}

function loadAll() {
  loadStats()
  loadAudit()
}

function clearFilters() {
  filters.email = ''
  filters.status = ''
  filters.from_date = ''
  filters.to_date = ''
  loadAudit()
}

function formatDate(isoStr) {
  if (!isoStr) return '—'
  const d = new Date(isoStr)
  return d.toLocaleString('es-GT', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  })
}

function getInitials(email) {
  if (!email) return '?'
  return email.substring(0, 2).toUpperCase()
}

function getStatusLabel(status) {
  const map = {
    'SUCCESS': 'Exitoso',
    'FAILED_INVALID_PASSWORD': 'Contraseña inválida',
    'FAILED_LOCKED': 'Bloqueado',
    'FAILED_USER_NOT_FOUND': 'No encontrado',
    'FAILED_INACTIVE': 'Inactivo'
  }
  return map[status] || status
}

function getStatusBadge(status) {
  const map = {
    'SUCCESS': 'bg-green-100 text-green-800',
    'FAILED_INVALID_PASSWORD': 'bg-amber-100 text-amber-800',
    'FAILED_LOCKED': 'bg-red-100 text-red-800',
    'FAILED_USER_NOT_FOUND': 'bg-gray-100 text-gray-800',
    'FAILED_INACTIVE': 'bg-purple-100 text-purple-800'
  }
  return map[status] || 'bg-gray-100 text-gray-800'
}

function exportCSV() {
  if (audit.value.length === 0) {
    toast.warning('No hay datos para exportar')
    return
  }
  
  const headers = ['Fecha', 'Email', 'Estado', 'IP', 'Motivo']
  const rows = audit.value.map(r => [
    formatDate(r.created_at),
    r.email_attempted,
    getStatusLabel(r.status),
    r.ip_address || '',
    r.failure_reason || ''
  ])
  
  const csv = [
    headers.join(','),
    ...rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
  ].join('\n')
  
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `bitacora-logins-${new Date().toISOString().split('T')[0]}.csv`
  link.click()
  
  toast.success('CSV exportado correctamente')
}

onMounted(() => {
  loadAll()
})
</script>