<!-- frontend/src/views/public/PublicRegister.vue -->
<template>
  <div class="min-h-screen flex items-center justify-center bg-linear-to-br from-blue-600 via-blue-700 to-emerald-600 p-4">
    <div class="bg-white p-8 rounded-2xl shadow-2xl w-full max-w-2xl">
      <!-- Header -->
      <div class="text-center mb-8">
        <div class="relative w-20 h-20 bg-linear-to-br from-blue-700 to-emerald-500 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
          <BookOpen class="w-10 h-10 text-white" />
          <div class="absolute -bottom-1 -right-1 w-8 h-8 bg-emerald-400 rounded-lg flex items-center justify-center shadow-md border-2 border-white">
            <BarChart3 class="w-5 h-5 text-white" />
          </div>
        </div>
        <h1 class="text-3xl font-bold text-gray-900">Solicitar Acceso a FastConta</h1>
        <p class="text-sm text-gray-600 mt-2">Complete el formulario y nos pondremos en contacto en 24-48h hábiles</p>
      </div>

      <!-- Success Message -->
      <div v-if="success" class="text-center py-8">
        <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <CheckCircle class="w-10 h-10 text-green-600" />
        </div>
        <h2 class="text-2xl font-bold text-gray-900 mb-2">¡Solicitud Enviada!</h2>
        <p class="text-gray-600 mb-6">
          Hemos recibido tu solicitud. Te contactaremos pronto para activar tu cuenta.
        </p>
        <router-link to="/login" class="text-blue-600 hover:text-blue-800 font-medium">
          Volver al Login
        </router-link>
      </div>

      <!-- Form -->
      <form v-else @submit.prevent="handleSubmit" class="space-y-6">
        <!-- Error Message -->
        <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {{ error }}
        </div>

        <!-- Datos de la Empresa -->
        <div class="border-b pb-4">
          <h3 class="text-lg font-semibold text-gray-800 mb-4">Datos de la Empresa</h3>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="md:col-span-2">
              <label class="block text-gray-700 text-sm font-bold mb-2">
                Nombre de la Empresa / Firma Contable *
              </label>
              <input
                v-model="form.company_name"
                type="text"
                required
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Ej: Contadores Asociados S.A."
              />
            </div>

            <div>
              <label class="block text-gray-700 text-sm font-bold mb-2">
                NIT *
              </label>
              <input
                v-model="form.nit"
                type="text"
                required
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="1234567-8"
              />
              <p class="text-xs text-gray-500 mt-1">Formato: 1234567-8 o 12345678-9</p>
            </div>

            <div>
              <label class="block text-gray-700 text-sm font-bold mb-2">
                Régimen Fiscal
              </label>
              <select
                v-model="form.regimen_fiscal_id"
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option :value="null">-- Seleccionar --</option>
                <option v-for="r in regimenes" :key="r.id" :value="r.id">
                  {{ r.nombre }}
                </option>
              </select>
            </div>

            <div>
              <label class="block text-gray-700 text-sm font-bold mb-2">
                Clientes Estimados
              </label>
              <input
                v-model.number="form.estimated_clients_count"
                type="number"
                min="1"
                max="1000"
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Ej: 50"
              />
            </div>
          </div>
        </div>

        <!-- Datos de Contacto -->
        <div class="border-b pb-4">
          <h3 class="text-lg font-semibold text-gray-800 mb-4">Datos de Contacto</h3>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="md:col-span-2">
              <label class="block text-gray-700 text-sm font-bold mb-2">
                Nombre Completo del Contacto *
              </label>
              <input
                v-model="form.contact_name"
                type="text"
                required
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Ej: Juan Pérez"
              />
            </div>

            <div>
              <label class="block text-gray-700 text-sm font-bold mb-2">
                Correo Electrónico *
              </label>
              <input
                v-model="form.contact_email"
                type="email"
                required
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="correo@empresa.com"
              />
              <p class="text-xs text-gray-500 mt-1">Este será el email del administrador</p>
            </div>

            <div>
              <label class="block text-gray-700 text-sm font-bold mb-2">
                Teléfono
              </label>
              <input
                v-model="form.contact_phone"
                type="tel"
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="5555-5555"
              />
            </div>
          </div>
        </div>

        <!-- Notas Adicionales -->
        <div>
          <label class="block text-gray-700 text-sm font-bold mb-2">
            Comentarios Adicionales
          </label>
          <textarea
            v-model="form.notes"
            rows="3"
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Cuéntanos sobre tu negocio o necesidades específicas..."
          ></textarea>
        </div>

        <!-- Submit Button -->
        <button
          type="submit"
          :disabled="loading"
          class="w-full bg-linear-to-r from-blue-700 to-emerald-600 text-white font-bold py-3 px-4 rounded-lg hover:from-blue-800 hover:to-emerald-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ loading ? 'Enviando...' : 'Enviar Solicitud' }}
        </button>

        <!-- Footer -->
        <div class="text-center text-sm text-gray-600">
          <p>¿Ya tienes una cuenta?</p>
          <router-link to="/login" class="text-blue-600 hover:text-blue-800 font-medium">
            Iniciar Sesión
          </router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { BookOpen, BarChart3, CheckCircle } from '@lucide/vue'
import { publicRegistrationApi } from '@/services/publicRegistration'
import publicApi from '@/services/publicApi'

const form = reactive({
  company_name: '',
  nit: '',
  contact_name: '',
  contact_email: '',
  contact_phone: '',
  regimen_fiscal_id: null,
  estimated_clients_count: null,
  notes: ''
})

const regimenes = ref([])
const loading = ref(false)
const error = ref('')
const success = ref(false)

const handleSubmit = async () => {
  loading.value = true
  error.value = ''
  try {
    await publicRegistrationApi.register(form)
    success.value = true
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al enviar la solicitud. Intenta nuevamente.'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    // ✅ CORREGIDO: Ruta correcta + parámetros + acceder a .data.data
    const response = await publicApi.get('/regimenes-fiscales/', {
      params: { is_active: true, limit: 200 }
    })
    regimenes.value = response.data.data || []
    
  } catch (err) {
    console.error('Error cargando regímenes:', err)
    console.error('Status:', err.response?.status)
    console.error('Data:', err.response?.data)
  }
})
</script>