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

        <!-- Tab: Estructura -->
        <div v-else-if="activeTab === 'estructura' && store.formularioActual">
          <FormularioDetail
            :formulario="store.formularioActual"
            :loading="store.loading"
            @editar="editarFormulario"
            @duplicar="abrirDuplicar"
            @agregar-seccion="toast.info('Próximamente: Agregar sección')"
            @editar-seccion="toast.info('Próximamente: Editar sección')"
            @eliminar-seccion="toast.info('Próximamente: Eliminar sección')"
            @agregar-casilla="toast.info('Próximamente: Agregar casilla')"
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

    <!-- Modal Crear/Editar -->
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useFormulariosStore } from '@/stores/formularios'
import { Plus } from '@lucide/vue'
import { toast } from 'vue3-toastify'

import FormularioList from '@/components/configuracion/formularios/FormularioList.vue'
import FormularioHistorialView from '@/components/configuracion/formularios/FormularioHistorialView.vue'
import FormularioDetail from '@/components/configuracion/formularios/FormularioDetail.vue'
import FormularioModal from '@/components/configuracion/formularios/FormularioModal.vue'
import FormularioDuplicarModal from '@/components/configuracion/formularios/FormularioDuplicarModal.vue'

const store = useFormulariosStore()

const activeTab = ref('todos')
const showCrearModal = ref(false)
const showEditarModal = ref(false)
const showDuplicarModal = ref(false)
const formularioSeleccionado = ref(null)

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
  
  console.log('📋 Formulario seleccionado:', formulario)
  
  // Cargar detalle completo (esto actualiza store.formularioActual)
  const result = await store.fetchFormularioDetail(formulario.id)
  
  console.log('✅ Resultado:', result)
  console.log('📑 Store.formularioActual:', store.formularioActual)
  console.log('📑 Secciones:', store.formularioActual?.secciones)
  
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

function cancelarModal() {
  showCrearModal.value = false
  showEditarModal.value = false
  showDuplicarModal.value = false
  formularioSeleccionado.value = null
}
</script>