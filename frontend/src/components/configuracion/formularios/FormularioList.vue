<template>
  <div v-if="loading" class="flex justify-center py-12">
    <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
  </div>

  <div v-else-if="formularios.length === 0" class="text-center py-12">
    <p class="text-gray-500">No hay formularios registrados</p>
  </div>

  <div v-else class="overflow-x-auto">
    <table class="min-w-full divide-y divide-gray-200">
      <thead class="bg-gray-50">
        <tr>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            Código
          </th>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            Versión
          </th>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            Nombre
          </th>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            Vigencia
          </th>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            Estado
          </th>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            Secciones
          </th>
          <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
            Acciones
          </th>
        </tr>
      </thead>
      <tbody class="bg-white divide-y divide-gray-200">
        <tr v-for="f in formularios" :key="f.id" class="hover:bg-gray-50">
          <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
            {{ f.codigo }}
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
            v{{ f.version }}
          </td>
          <td class="px-6 py-4 text-sm text-gray-700">
            <div class="font-medium">{{ f.nombre }}</div>
            <div v-if="f.descripcion" class="text-gray-500 text-xs mt-0.5 line-clamp-1">
              {{ f.descripcion }}
            </div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
            <div>{{ formatDate(f.fecha_vigencia_desde) }}</div>
            <div v-if="f.fecha_vigencia_hasta" class="text-gray-400 text-xs">
              hasta {{ formatDate(f.fecha_vigencia_hasta) }}
            </div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap">
            <span
              :class="[
                'px-2 py-1 text-xs font-medium rounded-full',
                f.es_version_activa
                  ? 'bg-green-100 text-green-800'
                  : 'bg-gray-100 text-gray-600'
              ]"
            >
              {{ f.es_version_activa ? 'Activo' : 'Inactivo' }}
            </span>
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
            {{ f.total_secciones || 0 }} secciones
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
            <button @click="$emit('ver', f)" class="text-blue-600 hover:text-blue-900 mr-3">
              Ver
            </button>
            <button @click="$emit('editar', f)" class="text-indigo-600 hover:text-indigo-900 mr-3">
              Editar
            </button>
            <button @click="$emit('duplicar', f)" class="text-amber-600 hover:text-amber-900 mr-3">
              Duplicar
            </button>
            <button @click="$emit('eliminar', f)" class="text-red-600 hover:text-red-900">
              Eliminar
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
defineProps({
  formularios: { type: Array, required: true },
  loading: { type: Boolean, default: false },
})

defineEmits(['ver', 'editar', 'duplicar', 'eliminar'])

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('es-GT')
}
</script>