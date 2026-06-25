<template>
  <div class="border border-gray-200 rounded-lg overflow-hidden">
    <!-- Header de la Sección -->
    <button
      @click="isOpen = !isOpen"
      :disabled="esSeccionAutomatica"
      :class="[
        'w-full px-4 py-3 flex items-center justify-between transition-colors',
        esSeccionAutomatica 
          ? 'bg-gray-100 cursor-default' 
          : 'bg-gray-50 hover:bg-gray-100'
      ]"
    >
      <div class="flex items-center gap-3">
        <span 
          :class="[
            'w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm',
            esSeccionAutomatica
              ? 'bg-gray-300 text-gray-600'
              : 'bg-blue-100 text-blue-700'
          ]"
        >
          {{ seccion.numero_seccion }}
        </span>
        <div class="text-left">
          <h3 class="font-semibold text-gray-800">
            {{ seccion.titulo }}
            <span v-if="esSeccionAutomatica" class="text-xs font-normal text-gray-500 ml-2">
              (Automática)
            </span>
          </h3>
          <p v-if="seccion.descripcion" class="text-xs text-gray-500 mt-0.5">
            {{ seccion.descripcion }}
          </p>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <span class="px-2 py-0.5 text-xs font-medium bg-gray-200 text-gray-700 rounded">
          {{ seccion.tipo_seccion }}
        </span>
        <span class="text-sm text-gray-500">
          {{ casillasOrdenadas.length }} casillas
        </span>
        <ChevronDown
          v-if="!esSeccionAutomatica"
          :class="['w-5 h-5 text-gray-400 transition-transform', isOpen ? 'rotate-180' : '']"
        />
        <Lock v-else class="w-5 h-5 text-gray-400" />
      </div>
    </button>

    <!-- Contenido de la Sección -->
    <div v-show="isOpen" class="p-4 bg-white border-t border-gray-200">
      <!-- Acciones de la sección (solo si NO es automática) -->
      <div v-if="!esSeccionAutomatica && editable" class="flex justify-end gap-2 mb-4">
        <button
          @click.stop="$emit('editar', seccion)"
          class="px-2 py-1 text-xs text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 rounded transition-colors"
        >
          Editar
        </button>
        <button
          @click.stop="$emit('eliminar', seccion)"
          class="px-2 py-1 text-xs text-red-600 hover:text-red-800 hover:bg-red-50 rounded transition-colors"
        >
          Eliminar
        </button>
      </div>

      <!-- Lista de Casillas -->
      <div class="space-y-3">
        <CasillaItem
          v-for="casilla in casillasOrdenadas"
          :key="casilla.id"
          :casilla="casilla"
          :editable="casilla.es_editable && editable && !esSeccionAutomatica"
          :valor-automatico="obtenerValorAutomatico(casilla.codigo)"
          @editar="$emit('editar-casilla', $event)"
          @eliminar="$emit('eliminar-casilla', $event)"
        />
      </div>

      <!-- Botón agregar casilla (solo si NO es automática) -->
      <button
        v-if="!esSeccionAutomatica && editable"
        @click.stop="$emit('agregar-casilla', { seccion_id: seccion.id, seccion_numero: seccion.numero_seccion, seccion_titulo: seccion.titulo })"
        class="mt-4 w-full px-4 py-2 border-2 border-dashed border-gray-300 rounded-lg text-sm text-gray-500 hover:border-blue-400 hover:text-blue-600 transition-colors flex items-center justify-center gap-2"
      >
        <Plus class="w-4 h-4" />
        Agregar casilla
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ChevronDown, Plus, Lock } from '@lucide/vue'
import CasillaItem from './CasillaItem.vue'

const props = defineProps({
  seccion: { type: Object, required: true },
  formularioId: { type: String, required: true },
  editable: { type: Boolean, default: true },
  datosEmpresa: { type: Object, default: null }, // NIT, nombre, etc.
  periodoDeclaracion: { type: Object, default: null }, // { mes, anio }
})

const isOpen = ref(true)

const esSeccionAutomatica = computed(() => {
  return ['1', '2'].includes(props.seccion.numero_seccion)
})

function obtenerValorAutomatico(codigo) {
  // Sección 1: NIT y Nombre
  if (props.seccion.numero_seccion === '1') {
    if (codigo === '1.1' && props.datosEmpresa) {
      return props.datosEmpresa.nit || ''
    }
    if (codigo === '1.2' && props.datosEmpresa) {
      return props.datosEmpresa.nombre || ''
    }
  }
  
  // Sección 2: Período
  if (props.seccion.numero_seccion === '2') {
    if (codigo === '2.1' && props.periodoDeclaracion) {
      const meses = {
        '1': 'Enero', '2': 'Febrero', '3': 'Marzo', '4': 'Abril',
        '5': 'Mayo', '6': 'Junio', '7': 'Julio', '8': 'Agosto',
        '9': 'Septiembre', '10': 'Octubre', '11': 'Noviembre', '12': 'Diciembre'
      }
      return meses[props.periodoDeclaracion.mes] || ''
    }
    if (codigo === '2.2' && props.periodoDeclaracion) {
      return props.periodoDeclaracion.anio || ''
    }
  }
  
  return null
}

const casillasOrdenadas = computed(() => {
  const casillas = props.seccion.casillas || []
  return [...casillas].sort((a, b) => {
    // Asegurar que orden_seccion sea número, default 0
    const ordenA = typeof a.orden_seccion === 'number' ? a.orden_seccion : 0
    const ordenB = typeof b.orden_seccion === 'number' ? b.orden_seccion : 0
    return ordenA - ordenB
  })
})
</script>