<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex justify-between items-center">
      <div>
        <h4 class="text-lg font-semibold text-gray-800">Representantes Legales</h4>
        <p class="text-sm text-gray-500">Personas autorizadas para representar a la empresa</p>
      </div>
      <button
        @click="abrirFormulario"
        class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1 shadow-sm"
      >
        <Plus class="w-4 h-4" />
        Agregar Representante
      </button>
    </div>

    <!-- Loading -->
    <div v-if="cargando" class="text-center py-6">
      <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
      <p class="mt-2 text-sm text-gray-500">Cargando representantes...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="representantes.length === 0" class="text-center py-8 bg-gray-50 rounded-lg border border-dashed border-gray-300">
      <Users class="w-10 h-10 text-gray-300 mx-auto" />
      <p class="mt-2 text-sm text-gray-500">No hay representantes legales registrados</p>
      <button @click="abrirFormulario" class="mt-2 text-blue-600 hover:text-blue-800 text-sm font-medium">
        + Agregar primer representante
      </button>
    </div>

    <!-- Lista de Representantes -->
    <div v-else class="space-y-3">
      <div
        v-for="rep in representantes"
        :key="rep.id"
        class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow"
      >
        <div class="flex justify-between items-start gap-4">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-2 flex-wrap">
              <span
                class="px-2 py-0.5 text-xs font-semibold rounded-full"
                :class="badgeColor(rep.tipo_identificacion)"
              >
                {{ rep.tipo_identificacion }}
              </span>
              <span class="text-xs text-gray-500 font-mono">
                {{ rep.numero_identificacion }}
              </span>
              <span v-if="!rep.es_activo" class="px-2 py-0.5 text-xs font-semibold rounded-full bg-gray-100 text-gray-600">
                Inactivo
              </span>
            </div>
            <p class="text-sm font-medium text-gray-900">{{ rep.nombre }}</p>
            <div class="flex items-center gap-3 mt-1 text-xs text-gray-500">
              <span v-if="rep.email" class="flex items-center gap-1">
                <Mail class="w-3 h-3" />
                {{ rep.email }}
              </span>
              <span v-if="rep.fecha_nombramiento" class="flex items-center gap-1">
                <Calendar class="w-3 h-3" />
                Nombrado: {{ formatearFecha(rep.fecha_nombramiento) }}
              </span>
            </div>
          </div>
          <div v-if="rep.es_activo" class="flex gap-2 flex-shrink-0">
            <button
              @click="editarRepresentante(rep)"
              class="text-blue-600 hover:text-blue-800 text-sm font-medium px-2 py-1 rounded hover:bg-blue-50"
            >
              Editar
            </button>
            <button
              @click="confirmarEliminar(rep)"
              class="text-red-600 hover:text-red-800 text-sm font-medium px-2 py-1 rounded hover:bg-red-50"
            >
              Eliminar
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Formulario Representante -->
    <div
      v-if="showForm"
      class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center z-50"
    >
      <div class="bg-white p-6 rounded-lg shadow-xl max-w-lg w-full mx-4 relative max-h-[90vh] overflow-y-auto">
        <button @click="cerrarFormulario" class="absolute top-4 right-4 text-gray-400 hover:text-gray-600">✕</button>

        <h3 class="text-lg font-bold mb-4 text-gray-800 pr-6">
          {{ modoEdicion ? 'Editar Representante' : 'Nuevo Representante Legal' }}
        </h3>

        <div v-if="errorForm" class="bg-red-100 border border-red-400 text-red-700 px-3 py-2 rounded mb-4 text-sm">
          {{ errorForm }}
        </div>

        <form @submit.prevent="guardarRepresentante" class="space-y-4">
          <!-- Nombre -->
          <div>
            <label class="block text-gray-700 text-sm font-bold mb-1">Nombre Completo *</label>
            <input
              v-model="form.nombre"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Ej: Juan Carlos Pérez López"
              required
            />
          </div>

          <!-- Tipo de Identificación -->
          <div>
            <label class="block text-gray-700 text-sm font-bold mb-1">Tipo de Identificación *</label>
            <select
              v-model="form.tipo_identificacion"
              @change="onTipoIdentificacionChange"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            >
              <option value="">-- Seleccionar --</option>
              <option v-for="tipo in tiposIdentificacion" :key="tipo" :value="tipo">
                {{ tipo }}
              </option>
            </select>
            <p class="text-xs text-gray-500 mt-1">{{ hintTipoIdentificacion }}</p>
          </div>

          <!-- Número de Identificación -->
          <div>
            <label class="block text-gray-700 text-sm font-bold mb-1">Número de Identificación *</label>
            <div class="relative">
              <input
                v-model="form.numero_identificacion"
                @input="debounceValidarIdentificacion"
                @blur="validarIdentificacion(form.numero_identificacion)"
                type="text"
                class="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                :class="{
                  'border-green-500': identificacionValida && form.numero_identificacion,
                  'border-red-500': !identificacionValida && form.numero_identificacion
                }"
                :placeholder="placeholderIdentificacion"
                required
              />
              <div v-if="validandoIdentificacion" class="absolute right-3 top-2.5">
                <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
              </div>
            </div>
            <p v-if="mensajeIdentificacion" class="text-xs mt-1" :class="identificacionValida ? 'text-green-600' : 'text-red-600'">
              {{ mensajeIdentificacion }}
            </p>
          </div>

          <!-- Fecha de Nombramiento -->
          <div>
            <label class="block text-gray-700 text-sm font-bold mb-1">Fecha de Nombramiento *</label>
            <input
              v-model="form.fecha_nombramiento_display"
              @input="formatearFechaInput"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="dd/mm/yyyy"
              maxlength="10"
              required
            />
            <p class="text-xs text-gray-500 mt-1">Formato: dd/mm/yyyy</p>
          </div>

          <!-- Email -->
          <div>
            <label class="block text-gray-700 text-sm font-bold mb-1">Email</label>
            <input
              v-model="form.email"
              type="email"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="correo@ejemplo.com"
            />
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
import { Plus, Users, Mail, Calendar } from '@lucide/vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  empresaId: { type: String, required: true },
  tenantId: { type: String, default: '' },
})

const emit = defineEmits(['updated'])
const authStore = useAuthStore()

// State
const representantes = ref([])
const cargando = ref(false)
const showForm = ref(false)
const modoEdicion = ref(false)
const representanteEditando = ref(null)
const guardando = ref(false)
const errorForm = ref('')

// Validación de identificación
const identificacionValida = ref(true)
const mensajeIdentificacion = ref('')
const validandoIdentificacion = ref(false)

// Form
const form = ref({
  nombre: '',
  tipo_identificacion: '',
  numero_identificacion: '',
  fecha_nombramiento: '',
  fecha_nombramiento_display: '',
  email: '',
})

// Tipos de identificación disponibles
const tiposIdentificacion = ['DPI', 'NIT', 'Pasaporte', 'Cédula']

// Hints dinámicos según tipo
const hintTipoIdentificacion = ref('Seleccione un tipo de identificación')
const placeholderIdentificacion = ref('Ingrese el número')

const params = () => {
  return props.tenantId ? { tenant_id: props.tenantId } : {}
}

// Badge color por tipo
const badgeColor = (tipo) => {
  const colors = {
    'DPI': 'bg-blue-100 text-blue-800',
    'NIT': 'bg-green-100 text-green-800',
    'Pasaporte': 'bg-purple-100 text-purple-800',
    'Cédula': 'bg-amber-100 text-amber-800',
  }
  return colors[tipo] || 'bg-gray-100 text-gray-800'
}

// Cambiar tipo de identificación
const onTipoIdentificacionChange = () => {
  const tipo = form.value.tipo_identificacion
  form.value.numero_identificacion = ''
  identificacionValida.value = true
  mensajeIdentificacion.value = ''

  if (tipo === 'DPI') {
    hintTipoIdentificacion.value = '13 dígitos (ej: 1234 56789 0101)'
    placeholderIdentificacion.value = '1234567890101'
  } else if (tipo === 'NIT') {
    hintTipoIdentificacion.value = 'Formato NIT guatemalteco (ej: 1234567-8)'
    placeholderIdentificacion.value = '1234567-8'
  } else if (tipo === 'Pasaporte') {
    hintTipoIdentificacion.value = 'Número de pasaporte'
    placeholderIdentificacion.value = 'A12345678'
  } else if (tipo === 'Cédula') {
    hintTipoIdentificacion.value = 'Número de cédula profesional'
    placeholderIdentificacion.value = '12345'
  } else {
    hintTipoIdentificacion.value = 'Seleccione un tipo de identificación'
    placeholderIdentificacion.value = 'Ingrese el número'
  }
}

// Formatear fecha dd/mm/yyyy
const formatearFechaInput = (event) => {
  let value = event.target.value.replace(/\D/g, '')
  if (value.length >= 2) {
    value = value.substring(0, 2) + '/' + value.substring(2)
  }
  if (value.length >= 5) {
    value = value.substring(0, 5) + '/' + value.substring(5, 9)
  }
  form.value.fecha_nombramiento_display = value
  
  if (value.length === 10) {
    const [dia, mes, anio] = value.split('/')
    form.value.fecha_nombramiento = `${anio}-${mes}-${dia}`
  } else {
    form.value.fecha_nombramiento = ''
  }
}

const formatearFecha = (fecha) => {
  if (!fecha) return ''
  const [anio, mes, dia] = fecha.split('-')
  return `${dia}/${mes}/${anio}`
}

// Debounce manual
let debounceTimerIdentificacion = null
const debounceValidarIdentificacion = () => {
  clearTimeout(debounceTimerIdentificacion)
  debounceTimerIdentificacion = setTimeout(() => {
    const numero = form.value.numero_identificacion
    const tipo = form.value.tipo_identificacion
    if (numero && numero.length >= 5 && tipo) {
      validarIdentificacion(numero)
    }
  }, 500)
}

// Validación de identificación (solo verifica formato en frontend, backend valida unicidad)
const validarIdentificacion = (numero) => {
  if (!numero || numero.length < 5) {
    identificacionValida.value = true
    mensajeIdentificacion.value = ''
    return
  }

  const tipo = form.value.tipo_identificacion
  let valido = true
  let mensaje = ''

  if (tipo === 'DPI') {
    const limpio = numero.replace(/\s/g, '')
    if (limpio.length !== 13 || !/^\d+$/.test(limpio)) {
      valido = false
      mensaje = '❌ DPI debe tener 13 dígitos numéricos'
    } else {
      mensaje = '✅ Formato DPI válido'
    }
  } else if (tipo === 'NIT') {
    // Validación básica de formato NIT
    const limpio = numero.replace(/\s/g, '')
    if (!/^\d{7,8}-?\d$/.test(limpio) && !/^\d{9}$/.test(limpio)) {
      valido = false
      mensaje = '❌ Formato NIT inválido (ej: 1234567-8 o 9 dígitos)'
    } else {
      mensaje = '✅ Formato NIT válido'
    }
  }

  identificacionValida.value = valido
  mensajeIdentificacion.value = mensaje
}

// Cargar representantes
const cargarRepresentantes = async () => {
  cargando.value = true
  try {
    const res = await api.get(`/empresas/${props.empresaId}/representantes/`, { params: params() })
    representantes.value = res.data || []
  } catch (err) {
    console.error('Error cargando representantes:', err)
  } finally {
    cargando.value = false
  }
}

// Abrir formulario (crear)
const abrirFormulario = () => {
  modoEdicion.value = false
  representanteEditando.value = null
  form.value = {
    nombre: '',
    tipo_identificacion: '',
    numero_identificacion: '',
    fecha_nombramiento: '',
    fecha_nombramiento_display: '',
    email: '',
  }
  identificacionValida.value = true
  mensajeIdentificacion.value = ''
  errorForm.value = ''
  showForm.value = true
}

// Editar representante
const editarRepresentante = (rep) => {
  modoEdicion.value = true
  representanteEditando.value = rep
  
  let fechaDisplay = ''
  if (rep.fecha_nombramiento) {
    const [anio, mes, dia] = rep.fecha_nombramiento.split('-')
    if (anio && mes && dia) {
      fechaDisplay = `${dia}/${mes}/${anio}`
    }
  }
  
  form.value = {
    nombre: rep.nombre,
    tipo_identificacion: rep.tipo_identificacion,
    numero_identificacion: rep.numero_identificacion,
    fecha_nombramiento: rep.fecha_nombramiento,
    fecha_nombramiento_display: fechaDisplay,
    email: rep.email || '',
  }
  
  // Actualizar hints
  onTipoIdentificacionChange()
  form.value.numero_identificacion = rep.numero_identificacion
  
  identificacionValida.value = true
  mensajeIdentificacion.value = ''
  errorForm.value = ''
  showForm.value = true
}

const cerrarFormulario = () => {
  showForm.value = false
  representanteEditando.value = null
  errorForm.value = ''
}

// Guardar
const guardarRepresentante = async () => {
  if (!identificacionValida.value && form.value.numero_identificacion) {
    errorForm.value = 'El número de identificación no tiene un formato válido.'
    return
  }
  
  guardando.value = true
  errorForm.value = ''

  try {
    const payload = {
      nombre: form.value.nombre,
      tipo_identificacion: form.value.tipo_identificacion,
      numero_identificacion: form.value.numero_identificacion,
      fecha_nombramiento: form.value.fecha_nombramiento,
      email: form.value.email || null,
    }

    if (modoEdicion.value && representanteEditando.value) {
      await api.put(
        `/empresas/${props.empresaId}/representantes/${representanteEditando.value.id}`,
        payload,
        { params: params() }
      )
    } else {
      await api.post(
        `/empresas/${props.empresaId}/representantes/`,
        payload,
        { params: params() }
      )
    }

    cerrarFormulario()
    await cargarRepresentantes()
    emit('updated')
  } catch (err) {
    const detail = err.response?.data?.detail || ''
    if (err.response?.status === 409) {
      errorForm.value = ` ${detail}`
    } else {
      errorForm.value = detail || 'Error al guardar representante'
    }
  } finally {
    guardando.value = false
  }
}

// Eliminar (soft delete)
const confirmarEliminar = async (rep) => {
  if (!confirm(`¿Eliminar al representante "${rep.nombre}"?\n\n${rep.tipo_identificacion}: ${rep.numero_identificacion}`)) return

  try {
    await api.delete(
      `/empresas/${props.empresaId}/representantes/${rep.id}`,
      { params: params() }
    )
    await cargarRepresentantes()
    emit('updated')
  } catch (err) {
    console.error('Error eliminando representante:', err)
  }
}

onMounted(() => {
  if (props.empresaId) {
    cargarRepresentantes()
  }
})

watch(() => props.empresaId, (newId) => {
  if (newId) cargarRepresentantes()
})
</script>