<template>
  <div class="p-6 max-w-7xl mx-auto">
    <!-- Header -->
    <div class="mb-6 flex justify-between items-center">
      <div>
        <h1 class="text-3xl font-bold text-gray-800 mb-1">Formularios SAT</h1>
        <p class="text-gray-600">Gestiona formularios y sus versiones</p>
      </div>
      <button
        @click="showCrearModal = true"
        class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2.5 rounded-lg font-medium transition-colors flex items-center gap-2 shadow-sm"
      >
        <Plus class="w-5 h-5" />
        Nuevo Formulario
      </button>
    </div>

    <!-- Tabs -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
      <div class="border-b border-gray-200">
        <nav class="flex -mb-px">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :disabled="tab.disabled"
            :class="[
              'px-6 py-4 text-sm font-medium border-b-2 transition-colors',
              tab.disabled ? 'opacity-50 cursor-not-allowed' : '',
              activeTab === tab.id
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            ]"
          >
            {{ tab.label }}
            <span
              v-if="tab.count !== undefined && tab.count !== null"
              :class="[
                'ml-2 px-2 py-0.5 text-xs rounded-full',
                activeTab === tab.id ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'
              ]"
            >
              {{ tab.count }}
            </span>
          </button>
        </nav>
      </div>

      <!-- Contenido -->
      <div class="p-6">
        <!-- Tab: Todos -->
        <div v-if="activeTab === 'todos'">
          <FormularioList
            :formularios="store.formularios"
            :loading="store.loading"
            @ver="verDetalle"
            @editar="editarFormulario"
            @duplicar="abrirDuplicar"
            @eliminar="confirmarEliminar"
          />
        </div>

        <!-- Tab: Activos -->
        <div v-else-if="activeTab === 'activos'">
          <FormularioList
            :formularios="store.formulariosActivos"
            :loading="store.loading"
            @ver="verDetalle"
            @editar="editarFormulario"
            @duplicar="abrirDuplicar"
            @eliminar="confirmarEliminar"
          />
        </div>

        <div v-else-if="activeTab === 'estructura' && store.formularioActual">
          <FormularioDetail
            :formulario="store.formularioActual"
            :loading="store.loading"
            @editar="editarFormulario"
            @duplicar="abrirDuplicar"
            @toggle-editable="toggleEditable"
            @agregar-seccion="abrirModalSeccion"
            @editar-seccion="abrirModalSeccion"
            @eliminar-seccion="confirmarEliminarSeccion"
            @agregar-casilla="abrirModalCasilla"
            @editar-casilla="abrirModalCasilla"
            @eliminar-casilla="confirmarEliminarCasilla"
          />
        </div>

        <!-- Tab: Historial -->
        <div v-else-if="activeTab === 'historial' && formularioSeleccionado">
          <FormularioHistorialView
            :codigo="formularioSeleccionado.codigo"
            :historial="store.historial"
            :loading="store.loading"
          />
        </div>
      </div>
    </div>

    <!-- Modal Crear/Editar Formulario -->
    <FormularioModal
      v-if="showCrearModal || showEditarModal"
      :titulo="showEditarModal ? 'Editar Formulario' : 'Nuevo Formulario'"
      :data="formularioSeleccionado"
      :loading="store.loading"
      @cancelar="cancelarModal"
      @guardar="guardarFormulario"
    />

    <!-- Modal Duplicar -->
    <FormularioDuplicarModal
      v-if="showDuplicarModal && formularioSeleccionado"
      :formulario="formularioSeleccionado"
      :loading="store.loading"
      @cancelar="showDuplicarModal = false"
      @duplicar="ejecutarDuplicar"
    />

    <!-- ✅ NUEVO: Modal Sección -->
    <SeccionModal
      v-if="showSeccionModal"
      :titulo="modoEdicionSeccion ? 'Editar Sección' : 'Nueva Sección'"
      :data="seccionSeleccionada"
      :formulario-id="store.formularioActual?.id"
      :formulario-codigo="store.formularioActual?.codigo"
      :loading="loadingSeccion"
      @cancelar="cerrarModalSeccion"
      @guardar="guardarSeccion"
    />

    <!-- ✅ NUEVO: Modal Casilla -->
    <CasillaModal
      v-if="showCasillaModal"
      :titulo="modoEdicionCasilla ? 'Editar Casilla' : 'Nueva Casilla'"
      :data="casillaSeleccionada"
      :loading="loadingCasilla"
      :seccion-id="seccionParaCasilla?.seccion_id"
      :seccion-numero="seccionParaCasilla?.numero_seccion || ''"
      :seccion-titulo="seccionParaCasilla?.titulo || ''"
      :siguiente-orden="seccionParaCasilla?.siguienteOrden"
      @cancelar="cerrarModalCasilla"
      @guardar="guardarCasilla"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useFormulariosStore } from '@/stores/formularios'
import { useSeccionesStore } from '@/stores/secciones'
import { useCasillasStore } from '@/stores/casillas'
import { Plus } from '@lucide/vue'
import { toast } from 'vue3-toastify'

import FormularioList from '@/components/configuracion/formularios/FormularioList.vue'
import FormularioHistorialView from '@/components/configuracion/formularios/FormularioHistorialView.vue'
import FormularioDetail from '@/components/configuracion/formularios/FormularioDetail.vue'
import FormularioModal from '@/components/configuracion/formularios/FormularioModal.vue'
import FormularioDuplicarModal from '@/components/configuracion/formularios/FormularioDuplicarModal.vue'
import SeccionModal from '@/components/configuracion/formularios/SeccionModal.vue'
import CasillaModal from '@/components/configuracion/formularios/CasillaModal.vue'

const store = useFormulariosStore()
const seccionesStore = useSeccionesStore()
const casillasStore = useCasillasStore()

const activeTab = ref('todos')
const showCrearModal = ref(false)
const showEditarModal = ref(false)
const showDuplicarModal = ref(false)
const formularioSeleccionado = ref(null)

// Estados para Secciones
const showSeccionModal = ref(false)
const seccionSeleccionada = ref(null)
const modoEdicionSeccion = ref(false)
const loadingSeccion = ref(false)

// Estados para Casillas
const showCasillaModal = ref(false)
const casillaSeleccionada = ref(null)
const modoEdicionCasilla = ref(false)
const seccionParaCasilla = ref(null)
const loadingCasilla = ref(false)

const tabs = computed(() => [
  { id: 'todos', label: 'Todos', count: store.total },
  { id: 'activos', label: 'Activos', count: store.formulariosActivos.length },
  {
    id: 'estructura',
    label: 'Estructura',
    count: store.formularioActual?.secciones?.length || 0,
    disabled: !store.formularioActual,
  },
  {
    id: 'historial',
    label: 'Historial',
    count: null,
    disabled: !formularioSeleccionado.value,
  },
])

onMounted(async () => {
  await store.fetchFormularios()
})

async function verDetalle(formulario) {
  formularioSeleccionado.value = formulario
  activeTab.value = 'estructura'
  
  const result = await store.fetchFormularioDetail(formulario.id) 

  if (!result.success) {
    toast.error(result.error)
  }
}

async function cargarHistorial(codigo) {
  const result = await store.fetchHistorial(codigo)
  if (!result.success) {
    toast.error(result.error)
  }
}

function editarFormulario(formulario) {
  formularioSeleccionado.value = formulario
  showEditarModal.value = true
}

function abrirDuplicar(formulario) {
  formularioSeleccionado.value = formulario
  showDuplicarModal.value = true
}

function confirmarEliminar(formulario) {
  if (confirm(`¿Está seguro de eliminar el formulario ${formulario.codigo} v${formulario.version}?`)) {
    eliminarFormulario(formulario)
  }
}

async function eliminarFormulario(formulario) {
  const result = await store.eliminarFormulario(formulario.id)
  if (result.success) {
    toast.success('Formulario eliminado exitosamente')
  } else {
    toast.error(result.error)
  }
}

async function guardarFormulario(data) {
  let result
  if (showEditarModal.value && formularioSeleccionado.value) {
    result = await store.actualizarFormulario(formularioSeleccionado.value.id, data)
  } else {
    result = await store.crearFormulario(data)
  }
  
  if (result?.success) {
    toast.success(result.message || 'Formulario guardado exitosamente')
    cancelarModal()
  } else {
    toast.error(result?.error || 'Error al guardar el formulario')
  }
}

async function ejecutarDuplicar(data) {
  if (formularioSeleccionado.value) {
    const result = await store.duplicarFormulario(formularioSeleccionado.value.id, data)
    if (result?.success) {
      toast.success(`Versión v${data.nueva_version} creada exitosamente`)
      showDuplicarModal.value = false
      formularioSeleccionado.value = null
    } else {
      toast.error(result?.error || 'Error al duplicar el formulario')
    }
  }
}

// === FUNCIONES DE SECCIÓN ===

function abrirModalSeccion(seccion = null) {
  seccionSeleccionada.value = seccion
  modoEdicionSeccion.value = !!seccion
  showSeccionModal.value = true
}

function cerrarModalSeccion() {
  showSeccionModal.value = false
  seccionSeleccionada.value = null
  modoEdicionSeccion.value = false
}

async function guardarSeccion(data) {
  loadingSeccion.value = true
  try {
    let result
    if (modoEdicionSeccion.value && seccionSeleccionada.value) {
      result = await seccionesStore.actualizarSeccion(seccionSeleccionada.value.id, data)
    } else {
      result = await seccionesStore.crearSeccion(data)
    }
    
    if (result.success) {
      toast.success('Sección guardada exitosamente')
      cerrarModalSeccion()
      // Recargar el formulario para ver los cambios
      if (store.formularioActual) {
        await store.fetchFormularioDetail(store.formularioActual.id)
      }
    } else {
      toast.error(result.error)
    }
  } catch (error) {
    console.error('Error al guardar sección:', error)
    toast.error('Error al guardar sección')
  } finally {
    loadingSeccion.value = false
  }
}

async function confirmarEliminarSeccion(seccion) {
  if (confirm(`¿Está seguro de eliminar la sección "${seccion.titulo}"?`)) {
    loadingSeccion.value = true
    const result = await seccionesStore.eliminarSeccion(seccion.id)
    if (result.success) {
      toast.success('Sección eliminada exitosamente')
      // Recargar el formulario
      if (store.formularioActual) {
        await store.fetchFormularioDetail(store.formularioActual.id)
      }
    } else {
      toast.error(result.error)
    }
    loadingSeccion.value = false
  }
}

// === FUNCIONES DE CASILLA ===

function abrirModalCasilla(payload) {
  // payload puede ser una casilla (editar) o un objeto { seccion_id, seccion_numero }
  if (payload && payload.id) {
    // Es edición
    casillaSeleccionada.value = payload
    modoEdicionCasilla.value = true
    // Buscar la sección de esta casilla
    if (store.formularioActual) {
      const seccion = store.formularioActual.secciones?.find(
        s => s.casillas?.some(c => c.id === payload.id)
      )
      seccionParaCasilla.value = {
        seccion_id: seccion?.id,
        seccion_numerio: seccion?.numero_seccion,
        seccion_titulo: seccion?.titulo,
      }
    }
  } else {
    // Es creación
    casillaSeleccionada.value = null
    modoEdicionCasilla.value = false
    
    // Calcular siguiente orden
    if (store.formularioActual && payload?.seccion_id) {
      const seccion = store.formularioActual.secciones?.find(
        s => s.id === payload.seccion_id
      )
      const maxOrden = Math.max(
        ...(seccion?.casillas?.map(c => c.orden_seccion) || [0])
      )
      seccionParaCasilla.value = {
        ...payload,
        siguienteOrden: maxOrden + 1,
      }
    } else {
      seccionParaCasilla.value = { ...payload, siguienteOrden: 0 }
    }
  }
  showCasillaModal.value = true

function cerrarModalCasilla() {
  showCasillaModal.value = false
  casillaSeleccionada.value = null
  modoEdicionCasilla.value = false
  seccionParaCasilla.value = null
}

async function guardarCasilla(data) {
  if (!seccionParaCasilla.value) {
    toast.error('No hay sección seleccionada')
    return
  }
  
  loadingCasilla.value = true
  try {
    const casillaData = {
      ...data,
      seccion_id: seccionParaCasilla.value.seccion_id,
    }
    
    let result
    if (modoEdicionCasilla.value && casillaSeleccionada.value) {
      result = await casillasStore.actualizarCasilla(casillaSeleccionada.value.id, casillaData)
    } else {
      result = await casillasStore.crearCasilla(casillaData)
    }
    
    if (result.success) {
      toast.success('Casilla guardada exitosamente')
      cerrarModalCasilla()
      // Recargar el formulario para ver los cambios
      if (store.formularioActual) {
        await store.fetchFormularioDetail(store.formularioActual.id)
      }
    } else {
      toast.error(result.error)
    }
  } catch (error) {
    console.error('Error al guardar casilla:', error)
    toast.error('Error al guardar casilla')
  } finally {
    loadingCasilla.value = false
  }
}

async function confirmarEliminarCasilla(casilla) {
  if (confirm(`¿Está seguro de eliminar la casilla "${casilla.nombre}"?`)) {
    loadingCasilla.value = true
    const result = await casillasStore.eliminarCasilla(casilla.id)
    if (result.success) {
      toast.success('Casilla eliminada exitosamente')
      // Recargar el formulario
      if (store.formularioActual) {
        await store.fetchFormularioDetail(store.formularioActual.id)
      }
    } else {
      toast.error(result.error)
    }
    loadingCasilla.value = false
  }
}

function cancelarModal() {
  showCrearModal.value = false
  showEditarModal.value = false
  showDuplicarModal.value = false
  formularioSeleccionado.value = null
}

async function toggleEditable(formulario) {
  const nuevoEstado = !formulario.editable
  const accion = nuevoEstado ? 'desbloquear' : 'bloquear'
  
  if (confirm(`¿Está seguro de ${accion} el formulario ${formulario.codigo} v${formulario.version}?`)) {
    const result = await store.actualizarFormulario(formulario.id, { editable: nuevoEstado })
    if (result.success) {
      toast.success(`Formulario ${nuevoEstado ? 'desbloqueado' : 'bloqueado'} exitosamente`)
      // Recargar detalle
      await store.fetchFormularioDetail(formulario.id)
    } else {
      toast.error(result.error)
    }
  }
}
</script>