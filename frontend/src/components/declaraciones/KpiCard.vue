<template>
  <div :class="['rounded-lg p-4', highlight ? 'bg-gradient-to-br from-green-500 to-green-600 text-white' : 'bg-gray-50']">
    <p :class="['text-xs uppercase tracking-wide', highlight ? 'text-green-100' : colorClass]">{{ label }}</p>
    <p :class="['text-2xl font-bold mt-1 font-mono', highlight ? '' : colorClass]">
      Q {{ Number(valor || 0).toLocaleString('es-GT', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
    </p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  valor: { type: Number, required: true },
  color: { type: String, default: 'gray' },
  highlight: { type: Boolean, default: false },
})

const colorClass = computed(() => {
  const colors = {
    red: 'text-red-600',
    blue: 'text-blue-600',
    yellow: 'text-yellow-600',
    green: 'text-green-600',
  }
  return colors[props.color] || 'text-gray-600'
})
</script>