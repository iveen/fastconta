<template>
  <div>
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <div v-else-if="!historial" class="text-center py-12">
      <p class="text-gray-500">No hay historial disponible</p>
    </div>

    <div v-else class="space-y-4">
      <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <h3 class="font-semibold text-blue-900">Código: {{ historial.codigo }}</h3>
        <p class="text-sm text-blue-700 mt-1">
          Total de versiones: {{ historial.total_versiones }}
        </p>
      </div>

      <div class="space-y-3">
        <div
          v-for="version in historial.versiones"
          :key="version.id"
          :class="[
            'p-4 rounded-lg border flex items-center justify-between',
            historial.version_actual?.id === version.id
              ? 'bg-green-50 border-green-300'
              : 'bg-white border-gray-200 hover:border-gray-300'
          ]"
        >
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <span class="text-blue-700 font-bold">v{{ version.version }}</span>
            </div>
            <div>
              <h4 class="font-semibold text-gray-900">{{ version.nombre }}</h4>
              <p class="text-sm text-gray-600">
                Vigencia: {{ formatDate(version.fecha_vigencia_desde) }}
                <span v-if="version.fecha_vigencia_hasta">
                  - {{ formatDate(version.fecha_vigencia_hasta) }}
                </span>
                <span v-else class="text-green-600 font-medium"> (Actual)</span>
              </p>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <span
              v-if="historial.version_actual?.id === version.id"
              class="px-3 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full"
            >
              ✓ Vigente
            </span>
            <span v-else class="px-3 py-1 text-xs font-medium bg-gray-100 text-gray-600 rounded-full">
              {{ version.total_secciones || 0 }} secciones
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  codigo: { type: String, required: true },
  historial: { type: Object, default: null },
  loading: { type: Boolean, default: false },
})

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('es-GT')
}
</script>