<!-- src/components/ToastContainer.vue -->
<template>
  <div class="fixed top-4 right-4 z-[9999] space-y-2 max-w-sm">
    <TransitionGroup
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="transform translate-x-full opacity-0"
      enter-to-class="transform translate-x-0 opacity-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="transform translate-x-0 opacity-100"
      leave-to-class="transform translate-x-full opacity-0"
    >
      <div
        v-for="toast in toasts"
        :key="toast.id"
        :class="toastClasses[toast.type]"
        class="flex items-start gap-3 px-4 py-3 rounded-lg shadow-lg border backdrop-blur-sm"
        role="alert"
      >
        <span class="text-lg">{{ toastIcons[toast.type] }}</span>
        <p class="flex-1 text-sm font-medium text-gray-900">{{ toast.message }}</p>
        <button
          @click="remove(toast.id)"
          class="text-gray-400 hover:text-gray-600 flex-shrink-0"
          aria-label="Cerrar"
        >
          ✕
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { useToast } from '@/composables/useToast'

const { toasts, remove } = useToast()

const toastClasses = {
  success: 'bg-green-50/95 border-green-200 text-green-800',
  error: 'bg-red-50/95 border-red-200 text-red-800',
  warning: 'bg-amber-50/95 border-amber-200 text-amber-800',
  info: 'bg-blue-50/95 border-blue-200 text-blue-800'
}

const toastIcons = {
  success: '✅',
  error: '❌',
  warning: '⚠️',
  info: 'ℹ️'
}
</script>