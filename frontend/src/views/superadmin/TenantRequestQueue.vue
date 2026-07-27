<template>
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
          <option value="rejected"> Rechazadas</option>
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
              <span class="font-semibold"> Clientes estimados:</span> {{ request.estimated_clients_count }}
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
            @click="openResendEmailModal(request)"
            class="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 font-medium transition-colors flex items-center gap-2"
            title="Reenviar email de confirmación"
          >
             Reenviar
          </button>
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

        <!-- Actions (para aprobadas - reenviar credenciales) -->
        <div v-else-if="request.status === 'approved'" class="flex gap-3 pt-4 border-t">
          <button
            @click="openResendCredentialsModal(request)"
            class="px-4 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 font-medium transition-colors flex items-center gap-2"
            title="Generar nueva contraseña y reenviar credenciales"
          >
            🔑 Reenviar credenciales
          </button>
          <div class="flex-1 text-sm text-gray-500 flex items-center">
            ✅ Aprobada el {{ formatDate(request.reviewed_at) }}
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Aprobar -->
    <!-- Reemplazar el modal de aprobación completo -->
    <div v-if="showApproveModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-lg p-6 w-full max-w-2xl shadow-2xl max-h-[90vh] overflow-y-auto">
        <h3 class="text-xl font-bold mb-4 text-gray-800">Aprobar Solicitud</h3>
        
        <!-- Info de la empresa -->
        <div class="bg-blue-50 border border-blue-200 rounded p-3 mb-4">
          <p class="text-sm text-blue-800">
            <strong>🏢 {{ selectedRequest?.company_name }}</strong><br>
            <span class="text-xs">NIT: {{ selectedRequest?.nit }}</span>
          </p>
        </div>

        <form @submit.prevent="handleApprove" class="space-y-4">
          <!-- Email del Admin -->
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

          <!-- Nombre del Admin -->
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

          <!-- 🆕 Selector de Plan con Sesiones Concurrentes -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Plan de Suscripción *</label>
            <div class="grid grid-cols-2 gap-3">
              <button
                v-for="plan in availablePlans"
                :key="plan.value"
                type="button"
                @click="selectPlan(plan.value)"
                class="p-3 border-2 rounded-lg text-left transition-all"
                :class="approveForm.plan === plan.value 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-gray-200 hover:border-gray-300'"
              >
                <div class="font-semibold text-sm text-gray-900">{{ plan.label }}</div>
                <div class="text-xs text-gray-500 mt-1">{{ plan.description }}</div>
                <div class="text-xs font-bold text-blue-600 mt-1">{{ plan.price }}</div>
              </button>
            </div>
          </div>

          <!--  Usuarios Registrados -->
          <div v-if="approveForm.plan !== 'freemium'">
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Usuarios Registrados *
            </label>
            <input
              v-model.number="approveForm.max_users_registered"
              type="number"
              :min="minUsersForPlan"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
            <p class="text-xs text-gray-500 mt-1">
              Mínimo {{ minUsersForPlan }} usuarios para plan {{ approveForm.plan }}
            </p>
          </div>

          <!-- 🆕 Ciclo de Facturación -->
          <div v-if="approveForm.plan !== 'freemium'">
            <label class="block text-sm font-medium text-gray-700 mb-1">Ciclo de Facturación</label>
            <select v-model="approveForm.billing_cycle" class="w-full px-3 py-2 border border-gray-300 rounded-lg">
              <option value="mensual">Mensual</option>
              <option value="trimestral">Trimestral (5% descuento)</option>
              <option value="anual">Anual (20% descuento)</option>
            </select>
          </div>

          <!-- 🆕 Días de Trial -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Días de Prueba</label>
            <input
              v-model.number="approveForm.trial_days"
              type="number"
              min="0"
              max="365"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
            <p class="text-xs text-gray-500 mt-1">0 = sin período de prueba</p>
          </div>

          <!-- 🆕 Resumen de Precio -->
          <div class="bg-green-50 border border-green-200 rounded p-3">
            <div class="flex justify-between items-center">
              <span class="font-medium text-sm text-green-900">Precio Mensual:</span>
              <span class="text-lg font-bold text-green-700">Q{{ calculateMonthlyPrice() }}</span>
            </div>
            <p class="text-xs text-green-600 mt-1">
              {{ approveForm.max_users_registered }} usuario(s) × Q{{ pricePerUser }}/mes
            </p>
          </div>

          <!-- Info de aprovisionamiento -->
          <div class="bg-yellow-50 border border-yellow-200 rounded p-3">
            <p class="text-xs text-yellow-800">
              ⚠️ <strong>Al aprobar:</strong> Se creará un schema PostgreSQL nuevo, 
              se ejecutarán las migraciones, y se <strong>generará automáticamente</strong> 
              una contraseña segura que se enviará por email al administrador.
            </p>
          </div>

          <!-- Botones -->
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
              {{ approving ? 'Aprobando...' : 'Aprobar' }}
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

    <!-- Modal Reenviar Email -->
    <div v-if="showResendEmailModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-lg p-6 w-full max-w-md shadow-2xl">
        <h3 class="text-xl font-bold mb-4 text-gray-800">📧 Reenviar Email de Confirmación</h3>
        
        <div class="bg-blue-50 border border-blue-200 rounded p-3 mb-4">
          <p class="text-sm text-blue-800">
            <strong>🏢 {{ selectedRequest?.company_name }}</strong><br>
            <span class="text-xs">NIT: {{ selectedRequest?.nit }}</span>
          </p>
        </div>
        
        <form @submit.prevent="handleResendEmail" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Email de Contacto *
            </label>
            <input
              v-model="resendEmailForm.contact_email"
              type="email"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              :placeholder="selectedRequest?.contact_email"
            />
            <p class="text-xs text-gray-500 mt-1">
              Email actual: <strong>{{ selectedRequest?.contact_email }}</strong>
            </p>
            <p v-if="resendEmailForm.contact_email !== selectedRequest?.contact_email" 
              class="text-xs text-amber-600 mt-1">
              ⚠️ El email será actualizado antes de reenviar
            </p>
          </div>
          
          <div class="bg-gray-50 border border-gray-200 rounded p-3">
            <p class="text-xs text-gray-600">
              ℹ️ Esto reenviará el email de confirmación con las instrucciones de registro.
            </p>
          </div>
          
          <div class="flex gap-3 pt-4">
            <button
              type="button"
              @click="showResendEmailModal = false"
              class="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400"
            >
              Cancelar
            </button>
            <button
              type="submit"
              :disabled="resendingEmail"
              class="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {{ resendingEmail ? 'Enviando...' : '📧 Reenviar' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- ✅ NUEVO: Modal Reenviar Credenciales -->
    <div v-if="showResendCredentialsModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-lg p-6 w-full max-w-md shadow-2xl">
        <h3 class="text-xl font-bold mb-4 text-gray-800">🔑 Reenviar Credenciales</h3>
        
        <div class="bg-blue-50 border border-blue-200 rounded p-3 mb-4">
          <p class="text-sm text-blue-800">
            <strong>🏢 {{ selectedRequest?.company_name }}</strong><br>
            <span class="text-xs">NIT: {{ selectedRequest?.nit }}</span>
          </p>
        </div>
        
        <div class="bg-amber-50 border border-amber-200 rounded p-3 mb-4">
          <p class="text-sm text-amber-800">
            ⚠️ <strong>Esta acción:</strong>
          </p>
          <ul class="text-xs text-amber-700 mt-2 list-disc list-inside space-y-1">
            <li>Generará una <strong>nueva contraseña segura</strong></li>
            <li>Invalidará la contraseña anterior</li>
            <li>Forzará al usuario a cambiarla en su próximo login</li>
            <li>Enviará las nuevas credenciales por email</li>
          </ul>
        </div>
        
        <div class="bg-gray-50 border border-gray-200 rounded p-3 mb-4">
          <p class="text-xs text-gray-600">
            ℹ️ Las credenciales se enviarán al email del administrador del tenant:
            <br><strong>{{ selectedRequest?.contact_email }}</strong>
          </p>
        </div>
        
        <div class="flex gap-3 pt-2">
          <button
            type="button"
            @click="showResendCredentialsModal = false"
            class="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400"
          >
            Cancelar
          </button>
          <button
            type="button"
            @click="handleResendCredentials"
            :disabled="resendingCredentials"
            class="flex-1 bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 disabled:opacity-50"
          >
            {{ resendingCredentials ? 'Generando...' : '🔑 Generar y Enviar' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

// Reemplazar el script setup completo
<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useSuperAdminStore } from '@/stores/superAdmin'
import { toast } from 'vue3-toastify'

const store = useSuperAdminStore()

const requests = ref([])
const statusFilter = ref('pending')
const loading = ref(false)
const showResendEmailModal = ref(false)
const resendingEmail = ref(false)
const showResendCredentialsModal = ref(false)
const resendingCredentials = ref(false)
const showApproveModal = ref(false)
const showRejectModal = ref(false)
const selectedRequest = ref(null)

// 🆕 Formulario de aprobación actualizado
const approveForm = reactive({
  admin_email: '',
  admin_full_name: '',
  plan: 'freemium',
  max_concurrent_sessions: 1,
  max_users_registered: 3,
  trial_days: 14,
  trial_max_concurrent_sessions: 1,
  trial_max_users_registered: 3,
  billing_cycle: 'mensual'
})

// 🆕 Planes disponibles con sesiones concurrentes
const availablePlans = [
  {
    value: 'freemium',
    label: 'Freemium',
    description: '1 sesión concurrente, 3 usuarios',
    price: 'Q0/mes',
    sessions: 1,
    minUsers: 1,
    pricePerUser: 0
  },
  {
    value: 'basico',
    label: 'Básico',
    description: '2 sesiones concurrentes',
    price: 'Q75/usuario/mes',
    sessions: 2,
    minUsers: 2,
    pricePerUser: 75
  },
  {
    value: 'profesional',
    label: 'Profesional',
    description: '5 sesiones concurrentes',
    price: 'Q60/usuario/mes',
    sessions: 5,
    minUsers: 5,
    pricePerUser: 60
  },
  {
    value: 'empresarial',
    label: 'Empresarial',
    description: '10 sesiones concurrentes',
    price: 'Q45/usuario/mes',
    sessions: 10,
    minUsers: 10,
    pricePerUser: 45
  }
]

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

const resendEmailForm = reactive({
  contact_email: ''
})

// 🆕 Computed properties para el formulario
const minUsersForPlan = computed(() => {
  const plan = availablePlans.find(p => p.value === approveForm.plan)
  return plan?.minUsers || 1
})

const pricePerUser = computed(() => {
  const plan = availablePlans.find(p => p.value === approveForm.plan)
  return plan?.pricePerUser || 0
})

// 🆕 Seleccionar plan
const selectPlan = (planValue) => {
  const plan = availablePlans.find(p => p.value === planValue)
  if (plan) {
    approveForm.plan = plan.value
    approveForm.max_concurrent_sessions = plan.sessions
    if (approveForm.max_users_registered < plan.minUsers) {
      approveForm.max_users_registered = plan.minUsers
    }
  }
}

//  Calcular precio mensual
const calculateMonthlyPrice = () => {
  if (approveForm.plan === 'freemium') return 0
  const monthly = approveForm.max_users_registered * pricePerUser.value
  
  if (approveForm.billing_cycle === 'trimestral') return (monthly * 3 * 0.95).toFixed(2)
  if (approveForm.billing_cycle === 'anual') return (monthly * 12 * 0.80).toFixed(2)
  return monthly.toFixed(2)
}

const openResendEmailModal = (request) => {
  selectedRequest.value = request
  resendEmailForm.contact_email = request.contact_email
  showResendEmailModal.value = true
}

const handleResendEmail = async () => {
  resendingEmail.value = true
  try {
    const newEmail = resendEmailForm.contact_email !== selectedRequest.value.contact_email 
      ? resendEmailForm.contact_email 
      : null

    await store.resendRequestEmail(selectedRequest.value.id, newEmail)
    showResendEmailModal.value = false
  } catch (err) {
    console.error('Error en handleResendEmail:', err)
  } finally {
    resendingEmail.value = false
  }
}

const openResendCredentialsModal = (request) => {
  selectedRequest.value = request
  showResendCredentialsModal.value = true
}

const handleResendCredentials = async () => {
  resendingCredentials.value = true
  try {
    const result = await store.resendTenantCredentials(selectedRequest.value.id)
    toast.success(`✅ ${result.message}`)
    showResendCredentialsModal.value = false
  } catch (err) {
    toast.error(err.response?.data?.detail || 'Error al reenviar credenciales')
  } finally {
    resendingCredentials.value = false
  }
}

const loadRequests = async () => {
  loading.value = true

  try {
    const result = await store.fetchTenantRequests(statusFilter.value)
    requests.value = result || []
  } catch (err) {
    console.error('Error cargando solicitudes:', err)
    toast.error('Error cargando la lista de solicitudes')
    requests.value = []
  } finally {
    loading.value = false
  }
}

// 🆕 Abrir modal de aprobación con valores por defecto
const openApproveModal = (request) => {
  selectedRequest.value = request
  approveForm.admin_email = request.contact_email
  approveForm.admin_full_name = request.contact_name
  approveForm.plan = 'freemium'
  approveForm.max_concurrent_sessions = 1
  approveForm.max_users_registered = 3
  approveForm.trial_days = 14
  approveForm.trial_max_concurrent_sessions = 1
  approveForm.trial_max_users_registered = 3
  approveForm.billing_cycle = 'mensual'
  showApproveModal.value = true
}

const openRejectModal = (request) => {
  selectedRequest.value = request
  rejectForm.reason = ''
  showRejectModal.value = true
}

// 🆕 Manejar aprobación con nuevo payload
const handleApprove = async () => {
  approving.value = true
  try {
    const result = await store.approveTenantRequest(selectedRequest.value.id, {
      admin_email: approveForm.admin_email,
      admin_full_name: approveForm.admin_full_name,
      plan: approveForm.plan,
      max_concurrent_sessions: approveForm.max_concurrent_sessions,
      max_users_registered: approveForm.max_users_registered,
      trial_days: approveForm.trial_days,
      trial_max_concurrent_sessions: approveForm.trial_max_concurrent_sessions,
      trial_max_users_registered: approveForm.trial_max_users_registered,
      billing_cycle: approveForm.billing_cycle
    })

    toast.success(`✅ ${result.message}`)
    showApproveModal.value = false
    await loadRequests()
  } catch (err) {
    toast.error(err.response?.data?.detail || 'Error al iniciar el provisionamiento')
  } finally {
    approving.value = false
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
  await loadRequests()
  await store.countPendingRequests()
})
</script>