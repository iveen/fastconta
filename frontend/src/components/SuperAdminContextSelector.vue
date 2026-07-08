<template>
  <div class="super-admin-context">
    <!-- Dropdown de Tenants -->
    <div class="context-group">
      <label>Tenant</label>
      <select 
        v-model="selectedTenantId" 
        @change="onTenantChange"
        :disabled="loadingTenants"
      >
        <option value="">Selecciona un tenant</option>
        <option 
          v-for="tenant in tenants" 
          :key="tenant.id" 
          :value="tenant.id"
        >
          {{ tenant.name }} ({{ tenant.nit }}) - {{ tenant.plan }}
        </option>
      </select>
    </div>

    <!-- Dropdown de Empresas -->
    <div class="context-group">
      <label>Empresa</label>
      <select 
        v-model="selectedEmpresaId" 
        @change="onEmpresaChange"
        :disabled="!selectedTenantId || loadingEmpresas"
      >
        <option value="">Selecciona una empresa</option>
        <option 
          v-for="empresa in empresas" 
          :key="empresa.id" 
          :value="empresa.id"
        >
          {{ empresa.nombre }} ({{ empresa.nit }})
        </option>
      </select>
      <span v-if="!selectedTenantId" class="hint">
        Selecciona primero un tenant
      </span>
      <span v-else-if="empresas.length === 0" class="hint warning">
        No hay empresas en este tenant
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useSuperAdminStore } from '@/stores/superAdmin'

const superAdminStore = useSuperAdminStore()

const tenants = ref([])
const empresas = ref([])
const selectedTenantId = ref('')
const selectedEmpresaId = ref('')
const loadingTenants = ref(false)
const loadingEmpresas = ref(false)

onMounted(async () => {
  await loadTenants()
})

async function loadTenants() {
  loadingTenants.value = true
  try {
    tenants.value = await superAdminStore.fetchTenants()
  } finally {
    loadingTenants.value = false
  }
}

async function onTenantChange() {
  selectedEmpresaId.value = ''
  empresas.value = []
  
  if (!selectedTenantId.value) return
  
  loadingEmpresas.value = true
  try {
    const response = await superAdminStore.fetchTenantEmpresas(selectedTenantId.value)
    empresas.value = response.empresas
  } finally {
    loadingEmpresas.value = false
  }
}

async function onEmpresaChange() {
  if (!selectedTenantId.value || !selectedEmpresaId.value) {
    superAdminStore.clearContext()
    return
  }
  
  await superAdminStore.setContext(
    selectedTenantId.value,
    selectedEmpresaId.value
  )
}
</script>

<style scoped>
.super-admin-context {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background: #f5f5f5;
  border-radius: 8px;
}

.context-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.context-group label {
  font-weight: 600;
  font-size: 0.875rem;
}

.context-group select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  min-width: 250px;
}

.hint {
  font-size: 0.75rem;
  color: #666;
}

.hint.warning {
  color: #f59e0b;
}
</style>