<template>
  <router-link
    :to="to"
    class="block p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 hover:shadow-md transition-all duration-200 group"
  >
    <div class="flex items-start gap-3">
      <span class="text-2xl flex-shrink-0">{{ icon }}</span>
      <div class="flex-1 min-w-0">
        <h3 class="font-semibold text-sm text-gray-800 group-hover:text-blue-600 transition-colors">
          {{ title }}
        </h3>
        <p class="text-xs text-gray-500 mt-1 line-clamp-2">
          {{ description }}
        </p>
      </div>
      <span class="text-gray-400 group-hover:text-blue-500 transition-colors flex-shrink-0">
        →
      </span>
    </div>
  </router-link>
</template>

<script setup>
defineProps({
  icon: {
    type: String,
    required: true
  },
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    required: true
  },
  to: {
    type: String,
    required: true
  }
})
</script>