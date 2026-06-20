<template>
  <div class="border border-gray-200 rounded-lg overflow-hidden">
    <!-- Header de la Sección -->
    <button
      @click="isOpen = !isOpen"
      class="w-full px-4 py-3 flex items-center justify-between bg-gray-50 hover:bg-gray-100 transition-colors"
    >
      <div class="flex items-center gap-3">
        <span class="w-8 h-8 bg-blue-100 text-blue-700 rounded-lg flex items-center justify-center font-bold text-sm">
          {{ seccion.numero_seccion }}
        </span>
        <div class="text-left">
          <h3 class="font-semibold text-gray-800">{{ seccion.titulo }}</h3>
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
          {{ seccion.total_casillas || 0 }} casillas
        </span>
        <ChevronDown 
          :class="['w-5 h-5 text-gray-400 transition-transform', isOpen ? 'rotate-180' : '']" 
        />
      </div>
    </button>

    <!-- Contenido de la Sección -->
    <div v-show="isOpen" class="p-4 bg-white border-t border-gray-200">
      <!-- Acciones de la sección -->
      <div class="flex justify-end gap-2 mb-4">
        <button 
          @click="$emit('editar', seccion)"
          class="px-2 py-1 text-xs text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 rounded transition-colors"
        >
          Editar
        </button>
        <button 
          @click="$emit('eliminar', seccion)"
          class="px-2 py-1 text-xs text-red-600 hover:text-red-800 hover:bg-red-50 rounded transition-colors"
        >
          Eliminar
        </button>
      </div>

      <!-- Lista de Casillas -->
      <div v-if="!seccion.casillas || seccion.casillas.length === 0" class="text-center py-4">
        <p class="text-sm text-gray-500">No hay casillas en esta sección</p>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        <CasillaItem
          v-for="casilla in casillasOrdenadas"
          :key="casilla.id"
          :casilla="casilla"
          @editar="$emit('editar-casilla', $event)"
          @eliminar="$emit('eliminar-casilla', $event)"
        />
      </div>

      <!-- Botón agregar casilla -->
      <button
        @click="$emit('agregar-casilla', { seccion_id: seccion.id, seccion_numero: seccion.numero_seccion })"
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
import { ChevronDown, Plus } from '@lucide/vue'
import CasillaItem from './CasillaItem.vue'

const props = defineProps({
  seccion: { type: Object, required: true },
  formularioId: { type: String, required: true },
})

defineEmits([
  'editar',
  'eliminar',
  'agregar-casilla',
  'editar-casilla',
  'eliminar-casilla',
])

const isOpen = ref(true)

const casillasOrdenadas = computed(() => 
  [...(props.seccion.casillas || [])].sort((a, b) => a.orden_seccion - b.orden_seccion)
)
</script>