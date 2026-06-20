<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200">
    <!-- Header del Formulario -->
    <div class="px-6 py-4 border-b border-gray-200 bg-gray-50 rounded-t-lg">
      <div class="flex justify-between items-start">
        <div>
          <div class="flex items-center gap-3 mb-2">
            <h2 class="text-xl font-bold text-gray-800">{{ formulario.nombre }}</h2>
            <span class="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-700 rounded-full">
              v{{ formulario.version }}
            </span>
            <span 
              v-if="formulario.es_version_activa"
              class="px-2 py-1 text-xs font-medium bg-green-100 text-green-700 rounded-full"
            >
              ✓ Vigente
            </span>
          </div>
          <p class="text-sm text-gray-600">{{ formulario.descripcion }}</p>
          <div class="flex items-center gap-4 mt-2 text-xs text-gray-500">
            <span>Código: {{ formulario.codigo }}</span>
            <span>•</span>
            <span>Vigencia: {{ formatDate(formulario.fecha_vigencia_desde) }} - {{ formatDate(formulario.fecha_vigencia_hasta) || 'Actual' }}</span>
            <span>•</span>
            <span>{{ secciones.length }} secciones</span>
            <span>•</span>
            <span>{{ totalCasillas }} casillas</span>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button 
            @click="$emit('editar', formulario)"
            class="px-3 py-1.5 text-sm text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 rounded-lg transition-colors"
          >
            Editar
          </button>
          <button 
            @click="$emit('duplicar', formulario)"
            class="px-3 py-1.5 text-sm text-amber-600 hover:text-amber-800 hover:bg-amber-50 rounded-lg transition-colors"
          >
            Duplicar Versión
          </button>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="p-8 flex justify-center">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>

    <!-- Secciones -->
    <div v-else class="p-6 space-y-4">
      <div v-if="!secciones || secciones.length === 0" class="text-center py-8 bg-gray-50 rounded-lg">
        <p class="text-gray-500 mb-2">Este formulario no tiene secciones configuradas</p>
        <button 
          @click="$emit('agregar-seccion')"
          class="text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          + Agregar primera sección
        </button>
      </div>

      <SeccionItem
        v-for="seccion in seccionesOrdenadas"
        :key="seccion.id"
        :seccion="seccion"
        :formulario-id="formulario.id"
        @editar="$emit('editar-seccion', $event)"
        @eliminar="$emit('eliminar-seccion', $event)"
        @agregar-casilla="$emit('agregar-casilla', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import SeccionItem from './SeccionItem.vue'

const props = defineProps({
  formulario: { type: Object, required: true },
  loading: { type: Boolean, default: false },
})

defineEmits([
  'editar',
  'duplicar',
  'agregar-seccion',
  'editar-seccion',
  'eliminar-seccion',
  'agregar-casilla',
])

// Debug: Ver qué recibe el componente
console.log('📦 FormularioDetail recibe:', props.formulario)

const secciones = computed(() => {
  const secs = props.formulario.secciones || []
  console.log(' Secciones en FormularioDetail:', secs)
  return secs
})

const seccionesOrdenadas = computed(() => 
  [...secciones.value].sort((a, b) => a.orden - b.orden)
)

const totalCasillas = computed(() => 
  secciones.value.reduce((sum, sec) => sum + (sec.casillas?.length || 0), 0)
)

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('es-GT')
}
</script>