<template>
  <div class="p-3 border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-sm transition-all group">
    <!-- Header de la Casilla -->
    <div class="flex items-start justify-between mb-2">
      <div class="flex items-center gap-2">
        <span class="px-2 py-0.5 text-xs font-mono font-medium bg-blue-50 text-blue-700 rounded">
          {{ casilla.codigo_visual || casilla.codigo }}
        </span>
        <h4 class="text-sm font-medium text-gray-800 line-clamp-1">{{ casilla.nombre }}</h4>
      </div>
      
      <div class="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
        <button 
          @click="$emit('editar', casilla)"
          class="p-1 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded transition-colors"
          title="Editar"
        >
          <Pencil class="w-3.5 h-3.5" />
        </button>
        <button 
          @click="$emit('eliminar', casilla)"
          class="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
          title="Eliminar"
        >
          <Trash2 class="w-3.5 h-3.5" />
        </button>
      </div>
    </div>

    <!-- Descripción -->
    <p v-if="casilla.descripcion" class="text-xs text-gray-500 mb-2 line-clamp-2">
      {{ casilla.descripcion }}
    </p>

    <!-- Tags de configuración -->
    <div class="flex flex-wrap gap-1.5">
      <span 
        :class="[
          'px-1.5 py-0.5 text-[10px] font-medium rounded',
          getTipoBadgeClass(casilla.tipo_casilla)
        ]"
      >
        {{ casilla.tipo_casilla }}
      </span>
      
      <span v-if="casilla.naturaleza" class="px-1.5 py-0.5 text-[10px] font-medium bg-gray-100 text-gray-700 rounded">
        {{ casilla.naturaleza }}
      </span>
      
      <span v-if="casilla.es_editable" class="px-1.5 py-0.5 text-[10px] font-medium bg-emerald-100 text-emerald-700 rounded">
        Editable
      </span>
      
      <span v-if="casilla.requiere_justificacion" class="px-1.5 py-0.5 text-[10px] font-medium bg-amber-100 text-amber-700 rounded">
        Requiere Justificación
      </span>
    </div>

    <!-- Campo origen (si existe) -->
    <p v-if="casilla.campo_origen_factura" class="text-[10px] text-gray-400 mt-2">
      Origen: <code class="bg-gray-100 px-1 rounded">{{ casilla.campo_origen_factura }}</code>
    </p>
  </div>
</template>

<script setup>
import { Pencil, Trash2 } from '@lucide/vue'

defineProps({
  casilla: { type: Object, required: true },
})

defineEmits(['editar', 'eliminar'])

function getTipoBadgeClass(tipo) {
  const classes = {
    'BASE_IMPONIBLE': 'bg-purple-100 text-purple-700',
    'DEBITO_FISCAL': 'bg-red-100 text-red-700',
    'CREDITO_FISCAL': 'bg-green-100 text-green-700',
    'REFERENCIA': 'bg-gray-100 text-gray-700',
    'CALCULADO': 'bg-blue-100 text-blue-700',
    'REMANENTE': 'bg-amber-100 text-amber-700',
    'AJUSTE': 'bg-orange-100 text-orange-700',
    'CONTEO': 'bg-teal-100 text-teal-700',
    'MANUAL': 'bg-pink-100 text-pink-700',
  }
  return classes[tipo] || 'bg-gray-100 text-gray-700'
}
</script>