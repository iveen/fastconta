<template>
  <div class="min-h-screen bg-gray-50 flex">
    <!-- Sidebar -->
    <aside class="w-64 bg-white border-r border-gray-200 p-4">
      <div class="mb-8">
        <h1 class="text-xl font-bold text-gray-900">FastConta</h1>
        <p class="text-xs text-gray-500">Superadmin</p>
      </div>
      
      <nav class="space-y-1">
        <RouterLink 
          to="/superadmin/tenants"
          class="block px-3 py-2 rounded-md text-sm font-medium"
          :class="$route.path.includes('/tenants') 
            ? 'bg-blue-50 text-blue-700' 
            : 'text-gray-700 hover:bg-gray-100'"
        >
          🏢 Tenants
        </RouterLink>
        <!-- Aquí irán más opciones en el futuro -->
      </nav>
    </aside>

    <!-- Contenido principal -->
    <main class="flex-1 p-6">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { RouterLink, RouterView, useRoute } from 'vue-router'

const $route = useRoute()
</script>