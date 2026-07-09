<template>
    <!-- Modal de Progreso -->
    <TenantProvisioningModal
    :is-visible="showProgressModal"
    :current-step="provisioningStep"
    @close="handleProgressClose"
    />
  <div class="max-w-7xl mx-auto">
    <!-- Header -->
    <div class="mb-6 flex justify-between items-center">
      <div>
        <h1 class="text-3xl font-bold text-gray-800">Solicitudes de Registro</h1>
        <p class="text-gray-600 mt-1">Gestiona las solicitudes de nuevas firmas contables</p>
      </div>
      <div class="flex gap-2">
        <select 
          v-model="statusFilter" 
          @change="loadRequests" 
          class="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        >
          <option :value="null">Todas</option>
          <option value="pending">⏳ Pendientes</option>
          <option value="approved">✅ Aprobadas</option>
          <option value="rejected">❌ Rechazadas</option>
        </select>
        <button 
          @click="loadRequests" 
          class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
          title="Recargar"
        >
          🔄
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="store.loading && requests.length === 0" class="text-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
      <p class="mt-4 text-gray-600">Cargando solicitudes...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="requests.length === 0" class="bg-white rounded-lg shadow p-12 text-center">
      <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
        <span class="text-3xl">📭</span>
      </div>
      <p class="text-gray-600 text-lg">No hay solicitudes {{ statusFilterLabel }}</p>
      <p class="text-gray-400 text-sm mt-2">
        Las solicitudes de registro aparecerán aquí para tu revisión
      </p>
    </div>

    <!-- Requests List -->
    <div v-else class="space-y-4">
      <div
        v-for="request in requests"
        :key="request.id"
        class="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6"
      >
        <!-- Header -->
        <div class="flex justify-between items-start mb-4">
          <div>
            <h3 class="text-xl font-bold text-gray-900">{{ request.company_name }}</h3>
            <p class="text-sm text-gray-600 font-mono">NIT: {{ request.nit }}</p>
          </div>
          <span
            :class="[
              'px-3 py-1 rounded-full text-xs font-semibold',
              statusBadgeClass(request.status)
            ]"
          >
            {{ statusLabel(request.status) }}
          </span>
        </div>

        <!-- Contact Info -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div class="space-y-1">
            <p class="text-sm text-gray-600">
              <span class="font-semibold">👤 Contacto:</span> {{ request.contact_name }}
            </p>
            <p class="text-sm text-gray-600">
              <span class="font-semibold">📧 Email:</span> 
              <a :href="`mailto:${request.contact_email}`" class="text-blue-600 hover:underline">
                {{ request.contact_email }}
              </a>
            </p>
            <p v-if="request.contact_phone" class="text-sm text-gray-600">
              <span class="font-semibold">📱 Teléfono:</span> {{ request.contact_phone }}
            </p>
          </div>
          <div class="space-y-1">
            <p v-if="request.estimated_clients_count" class="text-sm text-gray-600">
              <span class="font-semibold">👥 Clientes estimados:</span> {{ request.estimated_clients_count }}
            </p>
            <p class="text-sm text-gray-600">
              <span class="font-semibold">📅 Solicitado:</span> {{ formatDate(request.created_at) }}
            </p>
            <p v-if="request.reviewed_at" class="text-sm text-gray-600">
              <span class="font-semibold">🔍 Revisado:</span> {{ formatDate(request.reviewed_at) }}
            </p>
          </div>
        </div>

        <!-- Notes -->
        <div v-if="request.notes" class="bg-gray-50 p-3 rounded mb-4 border-l-4 border-gray-300">
          <p class="text-xs text-gray-500 font-semibold mb-1">📝 Notas del solicitante:</p>
          <p class="text-sm text-gray-700">{{ request.notes }}</p>
        </div>

        <!-- Actions (solo para pendientes) -->
        <div v-if="request.status === 'pending'" class="flex gap-3 pt-4 border-t">
          <button
            @click="openApproveModal(request)"
            class="flex-1 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 font-medium transition-colors"
          >
            ✅ Aprobar y Crear Tenant
          </button>
          <button
            @click="openRejectModal(request)"
            class="flex-1 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 font-medium transition-colors"
          >
            ❌ Rechazar
          </button>
        </div>
      </div>
    </div>

    <!-- Modal Aprobar -->
    <div v-if="showApproveModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-lg p-6 w-full max-w-lg shadow-2xl">
        <h3 class="text-xl font-bold mb-4 text-gray-800">Aprobar Solicitud</h3>
        
        <div class="bg-blue-50 border border-blue-200 rounded p-3 mb-4">
          <p class="text-sm text-blue-800">
            <strong>🏢 {{ selectedRequest?.company_name }}</strong><br>
            <span class="text-xs">NIT: {{ selectedRequest?.nit }}</span>
          </p>
        </div>

        <form @submit.prevent="handleApprove" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Email del Administrador *
            </label>
            <input
              v-model="approveForm.admin_email"
              type="email"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              :placeholder="selectedRequest?.contact_email"
            />
            <p class="text-xs text-gray-500 mt-1">Este será el usuario admin del nuevo tenant</p>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Nombre Completo del Admin *
            </label>
            <input
              v-model="approveForm.admin_full_name"
              type="text"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              :placeholder="selectedRequest?.contact_name"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Contraseña Temporal *
            </label>
            <input
              v-model="approveForm.admin_password"
              type="text"
              required
              minlength="8"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="Mínimo 8 caracteres"
            />
            <p class="text-xs text-gray-500 mt-1">El admin deberá cambiarla en su primer login</p>
          </div>
          
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Plan</label>
              <select v-model="approveForm.plan" class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                <option value="freemium">Freemium (3 usuarios)</option>
                <option value="basic">Basic (5 usuarios)</option>
                <option value="pro">Pro (10 usuarios)</option>
                <option value="enterprise">Enterprise (ilimitado)</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Max Usuarios</label>
              <input
                v-model.number="approveForm.max_usuarios"
                type="number"
                min="1"
                max="1000"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>
          </div>

          <div class="bg-yellow-50 border border-yellow-200 rounded p-3">
            <p class="text-xs text-yellow-800">
              ⚠️ <strong>Al aprobar:</strong> Se creará un schema PostgreSQL nuevo, 
              se ejecutarán todas las migraciones de tenant, y se creará el usuario admin.
            </p>
          </div>
          
          <div class="flex gap-3 pt-4">
            <button
              type="button"
              @click="showApproveModal = false"
              class="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400"
            >
              Cancelar
            </button>
            <button
              type="submit"
              :disabled="approving"
              class="flex-1 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              {{ approving ? 'Creando tenant...' : 'Aprobar' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal Rechazar -->
    <div v-if="showRejectModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-lg p-6 w-full max-w-md shadow-2xl">
        <h3 class="text-xl font-bold mb-4 text-gray-800">Rechazar Solicitud</h3>
        <form @submit.prevent="handleReject" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Razón del Rechazo *
            </label>
            <textarea
              v-model="rejectForm.reason"
              required
              minlength="5"
              rows="4"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500"
              placeholder="Explica por qué se rechaza la solicitud..."
            ></textarea>
            <p class="text-xs text-gray-500 mt-1">Mínimo 5 caracteres</p>
          </div>
          <div class="flex gap-3 pt-4">
            <button
              type="button"
              @click="showRejectModal = false"
              class="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400"
            >
              Cancelar
            </button>
            <button
              type="submit"
              :disabled="rejecting"
              class="flex-1 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 disabled:opacity-50"
            >
              {{ rejecting ? 'Rechazando...' : 'Rechazar' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useSuperAdminStore } from '@/stores/superAdmin'
import { toast } from 'vue3-toastify'
import TenantProvisionModal from '@/components/superadmin/TenantProvisionModal.vue'

const store = useSuperAdminStore()

// ✅ CORREGIDO: Definir todas las refs necesarias
const requests = ref([])
const statusFilter = ref('pending')
const loading = ref(false)  // ← ESTO FALTABA

const showApproveModal = ref(false)
const showRejectModal = ref(false)
const selectedRequest = ref(null)

// Estado del modal de progreso
const showProgressModal = ref(false)
const provisioningStep = ref({
  step: 1,
  total: 4,
  message: 'Iniciando...',
  status: 'pending'
})

const approveForm = reactive({
  admin_email: '',
  admin_full_name: '',
  admin_password: '',
  plan: 'freemium',
  max_usuarios: 3
})

const rejectForm = reactive({
  reason: ''
})

const approving = ref(false)
const rejecting = ref(false)

const statusFilterLabel = computed(() => {
  const labels = {
    pending: 'pendientes',
    approved: 'aprobadas',
    rejected: 'rechazadas'
  }
  return labels[statusFilter.value] || ''
})

// ✅ CORREGIDO: loadRequests ahora usa la ref local `loading`
const loadRequests = async () => {
  console.log('🔄 loadRequests: Iniciando carga...')
  loading.value = true
  
  try {
    console.log('🔄 loadRequests: Llamando a fetchTenantRequests con filtro:', statusFilter.value)
    const result = await store.fetchTenantRequests(statusFilter.value)
    console.log('🔄 loadRequests: Solicitudes recibidas:', result?.length || 0)
    requests.value = result || []
  } catch (err) {
    console.error('❌ loadRequests: Error cargando solicitudes:', err)
    console.error('❌ loadRequests: Detalles:', err.response?.data || err.message)
    toast.error('Error cargando la lista de solicitudes')
    requests.value = []
  } finally {
    loading.value = false
    console.log('🔄 loadRequests: Carga completada')
  }
}

const openApproveModal = (request) => {
  selectedRequest.value = request
  approveForm.admin_email = request.contact_email
  approveForm.admin_full_name = request.contact_name
  approveForm.admin_password = ''
  approveForm.plan = 'freemium'
  approveForm.max_usuarios = 3
  showApproveModal.value = true
}

const openRejectModal = (request) => {
  selectedRequest.value = request
  rejectForm.reason = ''
  showRejectModal.value = true
}

const handleApprove = async () => {
  console.log('🔍 Iniciando handleApprove')
  
  showProgressModal.value = true
  provisioningStep.value = {
    step: 1,
    total: 4,
    message: 'Iniciando...',
    status: 'processing'
  }
  
  try {
    const result = await store.approveTenantRequestWithProgress(
      selectedRequest.value.id,
      approveForm,
      (progress) => {
        console.log('📊 Progreso:', progress)
        provisioningStep.value = progress
      }
    )
    
    console.log('✅ Resultado recibido:', result)
    toast.success(`✅ Tenant "${result.tenant_name}" creado exitosamente`)
    showProgressModal.value = false
    showApproveModal.value = false
    await loadRequests()
  } catch (err) {
    console.error('❌ Error en handleApprove:', err)
    toast.error(err.response?.data?.detail || err.message || 'Error al crear el tenant')
    showProgressModal.value = false
  }
}

const handleReject = async () => {
  rejecting.value = true
  try {
    await store.rejectTenantRequest(selectedRequest.value.id, rejectForm.reason)
    toast.success('Solicitud rechazada')
    showRejectModal.value = false
    await loadRequests()
  } catch (err) {
    toast.error(err.response?.data?.detail || 'Error al rechazar solicitud')
  } finally {
    rejecting.value = false
  }
}

const statusBadgeClass = (status) => {
  const classes = {
    pending: 'bg-yellow-100 text-yellow-800 border border-yellow-300',
    approved: 'bg-green-100 text-green-800 border border-green-300',
    rejected: 'bg-red-100 text-red-800 border border-red-300'
  }
  return classes[status] || 'bg-gray-100 text-gray-800'
}

const handleProgressClose = () => {
  showProgressModal.value = false
  if (provisioningStep.value.status === 'error') {
    openApproveModal(selectedRequest.value)
  }
}

const statusLabel = (status) => {
  const labels = {
    pending: '⏳ Pendiente',
    approved: '✅ Aprobada',
    rejected: '❌ Rechazada'
  }
  return labels[status] || status
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('es-GT', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(async () => {
  console.log('📦 TenantRequestQueue mounted')
  await loadRequests()
  await store.countPendingRequests()
})
</script>