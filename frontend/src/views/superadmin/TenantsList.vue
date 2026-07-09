<template>
  <div class="max-w-7xl mx-auto">
    <!-- Header -->
    <div class="mb-6 flex justify-between items-center">
      <div>
        <h1 class="text-3xl font-bold text-gray-800">Gestión de Tenants</h1>
        <p class="text-gray-600 mt-1">Administra las firmas contables del sistema</p>
      </div>
      <button 
        @click="loadTenants" 
        class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
      >
        🔄 Recargar
      </button>
    </div>

    <!-- Loading -->
    <div v-if="store.loading && tenants.length === 0" class="text-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
    </div>

    <!-- Empty State -->
    <div v-else-if="tenants.length === 0" class="bg-white rounded-lg shadow p-12 text-center">
      <span class="text-5xl">🏢</span>
      <p class="text-gray-600 mt-4">No hay tenants registrados</p>
    </div>

    <!-- Tenants Table -->
    <div v-else class="bg-white rounded-lg shadow overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nombre</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">NIT</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Plan</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Usuarios</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Acciones</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="tenant in tenants" :key="tenant.id" class="hover:bg-gray-50">
            <td class="px-6 py-4">
              <div class="text-sm font-medium text-gray-900">{{ tenant.name }}</div>
              <div class="text-xs text-gray-500 font-mono">{{ tenant.schema_name }}</div>
            </td>
            <td class="px-6 py-4 text-sm text-gray-500 font-mono">{{ tenant.nit }}</td>
            <td class="px-6 py-4">
              <span class="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                {{ tenant.plan }}
              </span>
            </td>
            <td class="px-6 py-4 text-sm text-gray-500">
              {{ tenant.max_usuarios }}
              <span v-if="tenant.trial_until && isTrialActive(tenant)" class="text-xs text-amber-600 ml-1">
                (trial)
              </span>
            </td>
            <td class="px-6 py-4">
              <span
                :class="[
                  'px-2 py-1 text-xs font-semibold rounded-full',
                  tenant.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                ]"
              >
                {{ tenant.is_active ? '✅ Activo' : '❌ Inactivo' }}
              </span>
            </td>
            <td class="px-6 py-4 text-right text-sm font-medium space-x-2">
              <button
                v-if="tenant.is_active"
                @click="openDeactivateModal(tenant)"
                class="text-red-600 hover:text-red-900"
              >
                Desactivar
              </button>
              <button
                v-else
                @click="handleActivate(tenant)"
                class="text-green-600 hover:text-green-900"
              >
                Activar
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal Desactivar -->
    <div v-if="showDeactivateModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-lg p-6 w-full max-w-md shadow-2xl">
        <h3 class="text-xl font-bold mb-4 text-gray-800">Desactivar Tenant</h3>
        <div class="bg-red-50 border border-red-200 rounded p-3 mb-4">
          <p class="text-sm text-red-800">
            <strong>⚠️ ¿Desactivar "{{ selectedTenant?.name }}"?</strong><br>
            <span class="text-xs">Los usuarios de este tenant no podrán acceder al sistema.</span>
          </p>
        </div>
        <form @submit.prevent="handleDeactivate" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Razón de Desactivación *
            </label>
            <textarea
              v-model="deactivateForm.reason"
              required
              minlength="5"
              rows="3"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500"
              placeholder="Explica por qué se desactiva..."
            ></textarea>
          </div>
          <div class="flex gap-3 pt-4">
            <button
              type="button"
              @click="showDeactivateModal = false"
              class="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400"
            >
              Cancelar
            </button>
            <button
              type="submit"
              :disabled="deactivating"
              class="flex-1 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 disabled:opacity-50"
            >
              {{ deactivating ? 'Desactivando...' : 'Desactivar' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useSuperAdminStore } from '@/stores/superAdmin'
import { toast } from 'vue3-toastify'

const store = useSuperAdminStore()

const tenants = ref([])

const showDeactivateModal = ref(false)
const selectedTenant = ref(null)
const deactivateForm = reactive({ reason: '' })
const deactivating = ref(false)

const loadTenants = async () => {
  try {
    tenants.value = await store.fetchTenants()
  } catch (err) {
    toast.error('Error cargando tenants')
  }
}

const isTrialActive = (tenant) => {
  if (!tenant.trial_until) return false
  return new Date(tenant.trial_until) > new Date()
}

const openDeactivateModal = (tenant) => {
  selectedTenant.value = tenant
  deactivateForm.reason = ''
  showDeactivateModal.value = true
}

const handleDeactivate = async () => {
  deactivating.value = true
  try {
    await store.deactivateTenant(selectedTenant.value.id, deactivateForm.reason)
    toast.success('Tenant desactivado')
    showDeactivateModal.value = false
    await loadTenants()
  } catch (err) {
    toast.error(err.response?.data?.detail || 'Error al desactivar')
  } finally {
    deactivating.value = false
  }
}

const handleActivate = async (tenant) => {
  if (!confirm(`¿Reactivar "${tenant.name}"?`)) return
  
  try {
    await store.activateTenant(tenant.id)
    toast.success('Tenant reactivado')
    await loadTenants()
  } catch (err) {
    toast.error(err.response?.data?.detail || 'Error al reactivar')
  }
}

onMounted(loadTenants)
</script>