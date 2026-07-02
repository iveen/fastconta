<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex justify-between items-center">
      <div>
        <h4 class="text-lg font-semibold text-gray-800">Domicilios</h4>
        <p class="text-sm text-gray-500">Gestiona las direcciones de la empresa</p>
      </div>
      <button
        @click="abrirFormulario"
        class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1 shadow-sm"
      >
        <Plus class="w-4 h-4" />
        Agregar Domicilio
      </button>
    </div>

    <!-- Loading -->
    <div v-if="cargando" class="text-center py-6">
      <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
      <p class="mt-2 text-sm text-gray-500">Cargando domicilios...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="domicilios.length === 0" class="text-center py-8 bg-gray-50 rounded-lg border border-dashed border-gray-300">
      <MapPin class="w-10 h-10 text-gray-300 mx-auto" />
      <p class="mt-2 text-sm text-gray-500">No hay domicilios registrados</p>
      <button @click="abrirFormulario" class="mt-2 text-blue-600 hover:text-blue-800 text-sm font-medium">
        + Agregar primer domicilio
      </button>
    </div>

    <!-- Lista de Domicilios -->
    <div v-else class="space-y-3">
      <div
        v-for="domicilio in domicilios"
        :key="domicilio.id"
        class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow"
      >
        <div class="flex justify-between items-start gap-4">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-2 flex-wrap">
              <span
                class="px-2 py-0.5 text-xs font-semibold rounded-full"
                :class="badgeColor(domicilio.tipo_domicilio_nombre)"
              >
                {{ domicilio.tipo_domicilio_nombre || 'Sin tipo' }}
              </span>
              <span class="text-xs text-gray-400">
                {{ domicilio.departamento_nombre }} → {{ domicilio.municipio_nombre }}
              </span>
            </div>
            <p class="text-sm font-medium text-gray-900">{{ domicilio.direccion_exacta }}</p>
            <p class="text-xs text-gray-500 mt-1">
              <span v-if="domicilio.zona">Zona {{ domicilio.zona }}</span>
              <span v-if="domicilio.zona && domicilio.codigo_postal"> | </span>
              <span v-if="domicilio.codigo_postal">CP: {{ domicilio.codigo_postal }}</span>
            </p>
          </div>
          <div class="flex gap-2 flex-shrink-0">
            <button
              @click="editarDomicilio(domicilio)"
              class="text-blue-600 hover:text-blue-800 text-sm font-medium px-2 py-1 rounded hover:bg-blue-50"
            >
              Editar
            </button>
            <button
              @click="confirmarEliminar(domicilio)"
              class="text-red-600 hover:text-red-800 text-sm font-medium px-2 py-1 rounded hover:bg-red-50"
            >
              Eliminar
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Formulario Domicilio -->
    <div
      v-if="showForm"
      class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center z-50"
    >
      <div class="bg-white p-6 rounded-lg shadow-xl max-w-lg w-full mx-4 relative max-h-[90vh] overflow-y-auto">
        <button @click="cerrarFormulario" class="absolute top-4 right-4 text-gray-400 hover:text-gray-600">✕</button>

        <h3 class="text-lg font-bold mb-4 text-gray-800 pr-6">
          {{ modoEdicion ? 'Editar Domicilio' : 'Nuevo Domicilio' }}
        </h3>

        <div v-if="errorForm" class="bg-red-100 border border-red-400 text-red-700 px-3 py-2 rounded mb-4 text-sm">
          {{ errorForm }}
        </div>

        <form @submit.prevent="guardarDomicilio" class="space-y-4">
          <!-- Tipo de Domicilio -->
          <div>
            <label class="block text-gray-700 text-sm font-bold mb-1">Tipo de Domicilio *</label>
            <select
              v-model="form.tipo_domicilio_id"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            >
              <option value="">-- Seleccionar --</option>
              <option v-for="tipo in tiposDomicilio" :key="tipo.id" :value="tipo.id">
                {{ tipo.nombre }}
              </option>
            </select>
          </div>

          <!-- Departamento -->
          <div>
            <label class="block text-gray-700 text-sm font-bold mb-1">Departamento *</label>
            <select
              v-model="form.departamento_id"
              @change="onDepartamentoChange"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            >
              <option value="">-- Seleccionar --</option>
              <option v-for="dep in departamentos" :key="dep.id" :value="dep.id">
                {{ dep.nombre }}
              </option>
            </select>
          </div>

          <!-- Municipio -->
          <div>
            <label class="block text-gray-700 text-sm font-bold mb-1">Municipio *</label>
            <select
              v-model="form.municipio_id"
              :disabled="!form.departamento_id || cargandoMunicipios"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              required
            >
              <option value="">
                {{ cargandoMunicipios ? 'Cargando...' : (!form.departamento_id ? 'Seleccione un departamento primero' : '-- Seleccionar --') }}
              </option>
              <option v-for="mun in municipios" :key="mun.id" :value="mun.id">
                {{ mun.nombre }}
              </option>
            </select>
          </div>

          <!-- Dirección Exacta -->
          <div>
            <label class="block text-gray-700 text-sm font-bold mb-1">Dirección Exacta *</label>
            <textarea
              v-model="form.direccion_exacta"
              rows="2"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Ej: 5a Avenida 10-25, Edificio Torre Centro"
              required
            ></textarea>
          </div>

          <!-- Zona y Código Postal -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-gray-700 text-sm font-bold mb-1">Zona</label>
              <input
                v-model="form.zona"
                type="text"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Ej: 1"
              />
            </div>
            <div>
              <label class="block text-gray-700 text-sm font-bold mb-1">Código Postal</label>
              <input
                v-model="form.codigo_postal"
                type="text"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Ej: 01001"
              />
            </div>
          </div>

          <!-- Botones -->
          <div class="flex justify-end space-x-3 pt-4 border-t">
            <button
              type="button"
              @click="cerrarFormulario"
              class="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition"
            >
              Cancelar
            </button>
            <button
              type="submit"
              :disabled="guardando"
              class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition"
            >
              {{ guardando ? 'Guardando...' : (modoEdicion ? 'Actualizar' : 'Agregar') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { Plus, MapPin } from '@lucide/vue'
import api from '@/services/api'

const props = defineProps({
  empresaId: { type: String, required: true },
  tenantId: { type: String, default: '' },
})

const emit = defineEmits(['updated'])

// State
const domicilios = ref([])
const cargando = ref(false)
const showForm = ref(false)
const modoEdicion = ref(false)
const domicilioEditando = ref(null)
const guardando = ref(false)
const errorForm = ref('')

// Catálogos
const tiposDomicilio = ref([])
const departamentos = ref([])
const municipios = ref([])
const cargandoMunicipios = ref(false)

// Form
const form = ref({
  tipo_domicilio_id: '',
  departamento_id: '',
  municipio_id: '',
  direccion_exacta: '',
  zona: '',
  codigo_postal: '',
})

const params = () => {
  return props.tenantId ? { tenant_id: props.tenantId } : {}
}

// Badge color por tipo
const badgeColor = (tipo) => {
  const colors = {
    'FISCAL': 'bg-red-100 text-red-800',
    'SUCURSAL': 'bg-blue-100 text-blue-800',
    'OPERATIVO': 'bg-green-100 text-green-800',
    'BODEGA': 'bg-purple-100 text-purple-800',
  }
  return colors[tipo] || 'bg-gray-100 text-gray-800'
}

// Cargar catálogos
const cargarCatalogos = async () => {
  try {
    const [resTipos, resDeps] = await Promise.all([
      api.get('/geografia/tipos-domicilio'),
      api.get('/geografia/departamentos/todos'),
    ])
    tiposDomicilio.value = resTipos.data || []
    departamentos.value = resDeps.data || []
  } catch (err) {
    console.error('Error cargando catálogos de geografía:', err)
  }
}

// Cargar municipios al cambiar departamento
const onDepartamentoChange = async () => {
  form.value.municipio_id = ''
  municipios.value = []
  if (!form.value.departamento_id) return

  cargandoMunicipios.value = true
  try {
    const res = await api.get('/geografia/municipios', {
      params: { departamento_id: form.value.departamento_id },
    })
    municipios.value = res.data.data || []
  } catch (err) {
    console.error('Error cargando municipios:', err)
  } finally {
    cargandoMunicipios.value = false
  }
}

// Cargar domicilios
const cargarDomicilios = async () => {
  cargando.value = true
  try {
    const res = await api.get(`/empresas/${props.empresaId}/domicilios/`, { params: params() })
    domicilios.value = res.data || []
  } catch (err) {
    console.error('Error cargando domicilios:', err)
  } finally {
    cargando.value = false
  }
}

// Abrir formulario (crear)
const abrirFormulario = async () => {
  modoEdicion.value = false
  domicilioEditando.value = null
  form.value = {
    tipo_domicilio_id: '',
    departamento_id: '',
    municipio_id: '',
    direccion_exacta: '',
    zona: '',
    codigo_postal: '',
  }
  municipios.value = []
  errorForm.value = ''
  showForm.value = true
  await cargarCatalogos()
}

// Editar domicilio
const editarDomicilio = async (domicilio) => {
  modoEdicion.value = true
  domicilioEditando.value = domicilio
  errorForm.value = ''

  await cargarCatalogos()

  form.value = {
    tipo_domicilio_id: domicilio.tipo_domicilio_id,
    departamento_id: domicilio.departamento_id,
    municipio_id: domicilio.municipio_id,
    direccion_exacta: domicilio.direccion_exacta,
    zona: domicilio.zona || '',
    codigo_postal: domicilio.codigo_postal || '',
  }

  // Cargar municipios del departamento actual
  await onDepartamentoChange()
  // Restaurar el municipio seleccionado
  form.value.municipio_id = domicilio.municipio_id

  showForm.value = true
}

const cerrarFormulario = () => {
  showForm.value = false
  domicilioEditando.value = null
  errorForm.value = ''
}

// Guardar
const guardarDomicilio = async () => {
  guardando.value = true
  errorForm.value = ''

  try {
    const payload = { ...form.value }
    if (!payload.zona) payload.zona = null
    if (!payload.codigo_postal) payload.codigo_postal = null

    if (modoEdicion.value && domicilioEditando.value) {
      await api.put(
        `/empresas/${props.empresaId}/domicilios/${domicilioEditando.value.id}`,
        payload,
        { params: params() }
      )
    } else {
      await api.post(
        `/empresas/${props.empresaId}/domicilios/`,
        payload,
        { params: params() }
      )
    }

    cerrarFormulario()
    await cargarDomicilios()
    emit('updated')
  } catch (err) {
    errorForm.value = err.response?.data?.detail || 'Error al guardar domicilio'
  } finally {
    guardando.value = false
  }
}

// Eliminar
const confirmarEliminar = async (domicilio) => {
  const tipo = domicilio.tipo_domicilio_nombre || 'domicilio'
  if (!confirm(`¿Eliminar este domicilio (${tipo})?\n\n${domicilio.direccion_exacta}`)) return

  try {
    await api.delete(
      `/empresas/${props.empresaId}/domicilios/${domicilio.id}`,
      { params: params() }
    )
    await cargarDomicilios()
    emit('updated')
  } catch (err) {
    console.error('Error eliminando domicilio:', err)
  }
}

onMounted(() => {
  if (props.empresaId) {
    cargarDomicilios()
  }
})

watch(() => props.empresaId, (newId) => {
  if (newId) cargarDomicilios()
})
</script>