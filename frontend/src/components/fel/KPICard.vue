<template>
  <div :class="`bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow`">
    <div class="flex items-center justify-between mb-2">
      <span class="text-2xl">{{ icono }}</span>
      <span :class="`text-xs font-medium px-2 py-1 rounded-full ${colorClasses}`">
        {{ esNumero ? '' : 'GTQ' }}
      </span>
    </div>
    <p class="text-sm text-gray-500 mb-1">{{ titulo }}</p>
    <p :class="`text-2xl font-bold ${textColor}`">
      {{ esNumero ? valor.toLocaleString() : `Q ${Number(valor).toLocaleString('es-GT', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` }}
    </p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  titulo: String,
  valor: [Number, String],
  color: { type: String, default: 'blue' },
  icono: { type: String, default: '📊' },
  esNumero: { type: Boolean, default: false },
})

const colorMap = {
  blue: { bg: 'bg-blue-100', text: 'text-blue-800', border: 'text-blue-600' },
  green: { bg: 'bg-green-100', text: 'text-green-800', border: 'text-green-600' },
  red: { bg: 'bg-red-100', text: 'text-red-800', border: 'text-red-600' },
  purple: { bg: 'bg-purple-100', text: 'text-purple-800', border: 'text-purple-600' },
  orange: { bg: 'bg-orange-100', text: 'text-orange-800', border: 'text-orange-600' },
  teal: { bg: 'bg-teal-100', text: 'text-teal-800', border: 'text-teal-600' },
  indigo: { bg: 'bg-indigo-100', text: 'text-indigo-800', border: 'text-indigo-600' },
}

const colorClasses = computed(() => {
  const c = colorMap[props.color] || colorMap.blue
  return `${c.bg} ${c.text}`
})

const textColor = computed(() => {
  const c = colorMap[props.color] || colorMap.blue
  return c.border
})
</script>