<!-- src/views/Usuarios.vue -->
<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-6xl mx-auto space-y-6">
      <h1 class="text-2xl font-bold text-gray-800">Gestión de Usuarios y Accesos</h1>

      <!-- Banner de estado -->
      <div
        v-if="statusMsg"
        :class="statusType === 'error' ? 'bg-red-100 border-red-400 text-red-700' : 'bg-green-100 border-green-400 text-green-700'"
        class="border px-4 py-3 rounded flex justify-between items-center"
      >
        <span>{{ statusMsg }}</span>
        <button @click="statusMsg = ''" class="text-sm underline hover:no-underline">Cerrar</button>
      </div>
      <!-- 🔹 SELECTOR DE TENANT (Solo Superadmin) -->
      <div v-if="authStore.isSuperAdmin" class="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <label class="block text-sm font-semibold text-blue-800 mb-1">🏢 Seleccionar Firma (Tenant)</label>
        <select
          v-model="selectedTenantId"
          @change="handleTenantChange"
          class="w-full md:w-1/2 border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 p-2 border bg-white"
        >
          <option value="">-- Seleccione una firma para gestionar --</option>
          <option v-for="t in tenants" :key="t.id" :value="t.id">
            {{ t.name }} ({{ t.nit }})
          </option>
        </select>
      </div>

      <!-- SECCIÓN 1: Lista de Usuarios -->
      <div class="bg-white rounded-lg shadow overflow-hidden">
        <div class="px-6 py-4 border-b bg-gray-50 flex justify-between items-center">
          <h2 class="text-lg font-semibold text-gray-800">Usuarios del Tenant</h2>
          <button @click="showCreateForm = !showCreateForm" class="text-sm text-blue-600 hover:text-blue-800 font-medium">
            {{ showCreateForm ? 'Cancelar' : '+ Nuevo Usuario' }}
          </button>
        </div>

        <!-- Formulario de Creación (SIN CONTRASEÑA) -->
        <div v-if="showCreateForm" class="p-6 border-b bg-blue-50/50">
          <form @submit.prevent="handleCreateUser" class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Nombre Completo *</label>
              <input
                v-model="newUser.full_name"
                type="text"
                required
                class="w-full border-gray-300 rounded-md p-2 border"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Correo Electrónico *</label>
              <input
                v-model="newUser.email"
                type="email"
                required
                class="w-full border-gray-300 rounded-md p-2 border"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Rol *</label>
              <select v-model="newUser.role" required class="w-full border-gray-300 rounded-md p-2 border">
                <option value="tenant_member">Miembro del Tenant</option>
                <option value="tenant_manager">Administrador del Tenant</option>
                <option value="tenant_client">Cliente (Solo lectura)</option>
              </select>
            </div>

            <!-- Mensaje informativo sobre la contraseña automática -->
            <div class="md:col-span-2 bg-blue-50 border border-blue-200 rounded p-3">
              <p class="text-sm text-blue-800">
                ℹ️ <strong>Nota:</strong> No se requiere contraseña. Se generará una contraseña segura automáticamente
                y se enviará por email al usuario, quien deberá cambiarla en su primer inicio de sesión.
              </p>
            </div>

            <div class="md:col-span-2 flex justify-end gap-2 pt-2">
              <button
                type="button"
                @click="showCreateForm = false"
                class="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
              >
                Cancelar
              </button>
              <button
                type="submit"
                :disabled="loadingCreate"
                class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {{ loadingCreate ? 'Creando...' : 'Crear Usuario' }}
              </button>
            </div>
          </form>
        </div>

        <!-- Tabla de Usuarios -->
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nombre</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rol</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Acciones</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr
              v-for="u in users"
              :key="u.id"
              @click="selectUser(u)"
              :class="['cursor-pointer hover:bg-blue-50 transition', selectedUser?.id === u.id ? 'bg-blue-50 border-l-4 border-blue-500' : '']"
            >
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ u.full_name }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ u.email }}</td>

              <td class="px-6 py-4 whitespace-nowrap text-sm">
                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                  {{ formatRole(u.role) }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <!-- ✅ BOTÓN RESETEAR: Solo aparece si NO es el usuario logueado -->
                <button
                  v-if="u.public_id && u.public_id !== authStore.user?.public_id"
                  @click.stop="handleResetUserPassword(u)"
                  class="text-purple-600 hover:text-purple-900 mr-3"
                  title="Generar nueva contraseña y enviar por email"
                >
                  🔄 Resetear
                </button>
                <button @click.stop="selectUser(u)" class="text-blue-600 hover:text-blue-900">
                  Seleccionar
                </button>
              </td>
            </tr>
            <tr v-if="users.length === 0">
              <td colspan="4" class="px-6 py-8 text-center text-gray-500">No hay usuarios registrados.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- SECCIÓN 2: Empresas Asignadas -->
      <div v-if="selectedUser" class="bg-white rounded-lg shadow overflow-hidden border-2 border-blue-100">
        <div class="px-6 py-4 border-b bg-blue-50 flex justify-between items-center">
          <div>
            <h2 class="text-lg font-semibold text-gray-800">Empresas de: {{ selectedUser.full_name }}</h2>
            <p class="text-xs text-gray-500">ID: {{ selectedUser.id }}</p>
          </div>
          <button @click="selectedUser = null" class="text-sm text-gray-500 hover:text-gray-700">Cerrar panel</button>
        </div>

        <div class="p-6">
          <div class="flex flex-col md:flex-row gap-4 items-end mb-6 bg-gray-50 p-4 rounded-lg">
            <div class="flex-1 w-full">
              <label class="block text-sm font-medium text-gray-700 mb-1">Seleccionar Empresa</label>
              <select v-model="assignData.empresa_id" class="w-full border-gray-300 rounded-md p-2 border">
                <option value="">-- Selecciona una empresa --</option>
                <option v-for="emp in availableEmpresas" :key="emp.id" :value="emp.id">
                  {{ emp.nombre }} ({{ emp.nit }})
                </option>
              </select>
            </div>
            <button
              @click="handleAssignEmpresa"
              :disabled="!assignData.empresa_id || loadingAssign"
              class="w-full md:w-auto px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50"
            >
              {{ loadingAssign ? 'Asignando...' : '+ Asignar Empresa' }}
            </button>
          </div>

          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nombre de la Empresa</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">NIT</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="emp in userEmpresas" :key="emp.empresa_id">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ emp.nombre }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">{{ emp.nit }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                  <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                    Activo
                  </span>
                </td>
              </tr>
              <tr v-if="userEmpresas.length === 0">
                <td colspan="3" class="px-6 py-8 text-center text-gray-500 italic">
                  Este usuario no tiene empresas asignadas aún.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Modal de Confirmación para Resetear Contraseña -->
    <div
      v-if="showResetPasswordModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
    >
      <div class="bg-white rounded-lg p-6 w-full max-w-md shadow-2xl">
        <h3 class="text-xl font-bold mb-4 text-gray-800">🔄 Resetear Contraseña</h3>

        <div class="bg-blue-50 border border-blue-200 rounded p-3 mb-4">
          <p class="text-sm text-blue-800">
            <strong>👤 {{ selectedUser?.full_name }}</strong><br />
            <span class="text-xs">{{ selectedUser?.email }}</span>
          </p>
        </div>

        <div class="bg-amber-50 border border-amber-200 rounded p-3 mb-4">
          <p class="text-sm text-amber-800">⚠️ <strong>Esta acción:</strong></p>
          <ul class="text-xs text-amber-700 mt-2 list-disc list-inside space-y-1">
            <li>Generará una <strong>nueva contraseña segura</strong> automáticamente</li>
            <li>Invalidará la contraseña anterior inmediatamente</li>
            <li>Enviará la nueva contraseña por email al usuario</li>
            <li>Forzará al usuario a cambiarla en su próximo login</li>
          </ul>
        </div>

        <div class="flex gap-3 pt-2">
          <button
            type="button"
            @click="showResetPasswordModal = false"
            class="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400"
          >
            Cancelar
          </button>
          <button
            type="button"
            @click="confirmResetPassword"
            :disabled="resettingPassword"
            class="flex-1 bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 disabled:opacity-50"
          >
            {{ resettingPassword ? 'Procesando...' : '🔄 Generar y Enviar' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'
import { toast } from 'vue3-toastify'

const authStore = useAuthStore()

const tenants = ref([])
const selectedTenantId = ref('')
const users = ref([])
const availableEmpresas = ref([])
const selectedUser = ref(null)
const userEmpresas = ref([])

const showCreateForm = ref(false)
const loadingCreate = ref(false)
const loadingAssign = ref(false)
const statusMsg = ref('')
const statusType = ref('success')

const showResetPasswordModal = ref(false)
const resettingPassword = ref(false)

const newUser = ref({
  full_name: '',
  email: '',
  role: 'tenant_member'
})

const assignData = ref({ empresa_id: '' })

const formatRole = (role) => {
  const map = {
    superadmin: 'Super Administrador',
    tenant_manager: 'Admin. Tenant',
    tenant_member: 'Miembro',
    tenant_client: 'Cliente'
  }
  return map[role] || role
}

// 🔹 Cargar lista de tenants solo si es superadmin
const fetchTenants = async () => {
  if (!authStore.isSuperAdmin) return
  try {
    const res = await api.get('/tenants/')
    // Filtrar cualquier tenant con schema_name 'sistema' o 'system' (defensa en profundidad)
    tenants.value = res.data.filter((t) => !['sistema', 'system', 'public'].includes(t.schema_name))
  } catch (err) {
    console.error('Error cargando tenants:', err)
  }
}

const fetchData = async () => {
  // Si es superadmin, debe haber un tenant seleccionado
  const targetTenantId = authStore.isSuperAdmin ? selectedTenantId.value : null

  if (authStore.isSuperAdmin && !targetTenantId) {
    users.value = []
    availableEmpresas.value = []
    return
  }

  try {
    const params = targetTenantId ? { tenant_id: targetTenantId } : {}
    const [usersRes, empRes] = await Promise.all([
      api.get('/users/', { params }),
      api.get('/empresas/', { params })
    ])
    users.value = usersRes.data
    availableEmpresas.value = empRes.data
  } catch (err) {
    statusMsg.value = 'Error al cargar datos: ' + (err.response?.data?.detail || err.message)
    statusType.value = 'error'
  }
}

const handleTenantChange = () => {
  selectedUser.value = null // Limpiar selección al cambiar de tenant
  userEmpresas.value = []
  fetchData()
}

const selectUser = async (user) => {
  selectedUser.value = user
  userEmpresas.value = []
  assignData.value.empresa_id = ''
  try {
    const res = await api.get(`/users/${user.public_id}/empresas`)
    userEmpresas.value = res.data
  } catch (err) {
    console.error('Error cargando empresas del usuario:', err)
  }
}

const handleCreateUser = async () => {
  loadingCreate.value = true
  statusMsg.value = ''

  try {
    // ✅ CORREGIDO: Construir el payload limpiamente (sin password)
    const payload = {
      full_name: newUser.value.full_name,
      email: newUser.value.email,
      role: newUser.value.role
    }

    // Asignar tenant_id correctamente según el rol del usuario logueado
    if (authStore.isSuperAdmin) {
      payload.tenant_id = parseInt(selectedTenantId.value)
    } else {
      // Si es tenant_manager, usamos el tenant_id del usuario autenticado
      payload.tenant_id = authStore.user?.tenant_id
    }

    await api.post('/users/', payload)

    statusMsg.value = '✅ Usuario creado exitosamente. Se ha enviado un email con las credenciales.'
    statusType.value = 'success'

    // Resetear formulario
    newUser.value = { full_name: '', email: '', role: 'tenant_member' }
    showCreateForm.value = false
    await fetchData()
  } catch (err) {
    statusMsg.value = '❌ ' + (err.response?.data?.detail || err.message)
    statusType.value = 'error'
  } finally {
    loadingCreate.value = false
  }
}

const handleAssignEmpresa = async () => {
  if (!selectedUser.value || !assignData.value.empresa_id) return

  loadingAssign.value = true
  statusMsg.value = ''

  try {
    await api.post(`/users/${selectedUser.value.public_id}/empresas`, { empresa_id: assignData.value.empresa_id })
    statusMsg.value = '✅ Empresa asignada correctamente.'
    statusType.value = 'success'
    assignData.value.empresa_id = ''
    await selectUser(selectedUser.value)
  } catch (err) {
    statusMsg.value = '❌ ' + (err.response?.data?.detail || err.message)
    statusType.value = 'error'
  } finally {
    loadingAssign.value = false
  }
}

// ✅ NUEVO: Resetear contraseña de usuario
const handleResetUserPassword = (user) => {
  console.log(selectUser)
  selectedUser.value = user
  showResetPasswordModal.value = true
}

const confirmResetPassword = async () => {
  if (!selectedUser.value) return
  console.log("Reset", selectedUser.value)
  resettingPassword.value = true
  try {
    await api.post(`/auth/reset-password?user_id=${selectedUser.value.public_id}`)
    toast.success(`✅ Contraseña reseteada. Se ha enviado un email a ${selectedUser.value.email}`)
    showResetPasswordModal.value = false
  } catch (err) {
    toast.error(err.response?.data?.detail || 'Error al resetear contraseña')
  } finally {
    resettingPassword.value = false
  }
}

onMounted(async () => {
  await fetchTenants()
  // Si es superadmin, preseleccionar el primer tenant para UX inmediata
  if (authStore.isSuperAdmin && tenants.value.length > 0) {
    selectedTenantId.value = tenants.value[0].id
  }
  await fetchData()
})
</script>