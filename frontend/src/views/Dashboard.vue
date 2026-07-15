<!-- src/views/Dashboard.vue -->
<template>
  <div class="min-h-screen flex bg-gray-50">
    <Sidebar />
    
    <div class="flex-1 flex flex-col">
      <TopNavbar />
      
      <main class="flex-1 p-6">
        <router-view />
      </main>
    </div>
    
    <ToastContainer />
  </div>
</template>

<script setup>
import Sidebar from '@/components/Sidebar.vue'
import TopNavbar from '@/components/TopNavbar.vue'
import ToastContainer from './ToastContainer.vue'
</script>